package org.zetamesh.gnss;

import android.app.Activity;
import android.app.Instrumentation;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothManager;
import android.bluetooth.BluetoothProfile;
import android.bluetooth.BluetoothStatusCodes;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanFilter;
import android.bluetooth.le.ScanResult;
import android.bluetooth.le.ScanSettings;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Bundle;
import android.os.ParcelUuid;
import android.os.SystemClock;

import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;

public final class TrekkingProbe extends Instrumentation {
    private static final UUID SERVICE = UUID.fromString("c142b720-fb05-4aa1-a203-a4bd332c1e41");
    private static final UUID VALUE = UUID.fromString("c142b721-fb05-4aa1-a203-a4bd332c1e41");
    private Bundle arguments;

    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        arguments = args == null ? new Bundle() : args;
        start();
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            String mode = arguments.getString("mode", "battery");
            if ("battery".equals(mode)) {
                battery(result);
            } else if ("ble".equals(mode)) {
                int count = Integer.parseInt(arguments.getString("count", "20"));
                if (count < 1 || count > 100) throw new ProbeFailure("count_must_be_1_to_100");
                ble(result, count);
            } else {
                throw new ProbeFailure("unknown_mode");
            }
            finish(Activity.RESULT_OK, result);
        } catch (Exception error) {
            result.putString("error", error instanceof ProbeFailure
                    ? error.getMessage() : error.getClass().getSimpleName());
            finish(Activity.RESULT_CANCELED, result);
        }
    }

    private void battery(Bundle result) {
        Context context = getTargetContext();
        BatteryManager manager = context.getSystemService(BatteryManager.class);
        int charge = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CHARGE_COUNTER);
        int percent = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
        long energy = manager.getLongProperty(BatteryManager.BATTERY_PROPERTY_ENERGY_COUNTER);
        result.putString("charge_uah", charge == Integer.MIN_VALUE ? "unsupported" : Integer.toString(charge));
        result.putString("battery_percent", percent == Integer.MIN_VALUE ? "unsupported" : Integer.toString(percent));
        result.putString("energy_nwh", energy == Long.MIN_VALUE ? "unsupported" : Long.toString(energy));
        result.putLong("elapsed_ms", SystemClock.elapsedRealtime());
        Intent sticky = context.registerReceiver(null, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        int plugged = sticky == null ? -1 : sticky.getIntExtra(BatteryManager.EXTRA_PLUGGED, -1);
        result.putString("external_power", plugged < 0 ? "unknown" : plugged == 0 ? "no" : "yes");
    }

    private BluetoothDevice findPeer(BluetoothLeScanner scanner) throws Exception {
        BlockingQueue<ScanResult> results = new ArrayBlockingQueue<>(1);
        BlockingQueue<Integer> failures = new ArrayBlockingQueue<>(1);
        ScanCallback callback = new ScanCallback() {
            @Override public void onScanResult(int type, ScanResult result) { results.offer(result); }
            @Override public void onScanFailed(int error) { failures.offer(error); }
        };
        ScanFilter filter = new ScanFilter.Builder().setServiceUuid(new ParcelUuid(SERVICE)).build();
        ScanSettings settings = new ScanSettings.Builder()
                .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build();
        scanner.startScan(Collections.singletonList(filter), settings, callback);
        try {
            for (int second = 0; second < 10; second++) {
                Integer error = failures.poll();
                if (error != null) throw new ProbeFailure("scan_failed_" + error);
                ScanResult found = results.poll(1, TimeUnit.SECONDS);
                if (found != null) return found.getDevice();
            }
            throw new ProbeFailure("peer_not_found");
        } finally {
            scanner.stopScan(callback);
        }
    }

    private void ble(Bundle result, int count) throws Exception {
        Context context = getTargetContext();
        BluetoothAdapter adapter = context.getSystemService(BluetoothManager.class).getAdapter();
        BluetoothLeScanner scanner = adapter == null ? null : adapter.getBluetoothLeScanner();
        if (scanner == null) throw new ProbeFailure("ble_unavailable_or_off");
        BluetoothDevice device = findPeer(scanner);
        GattEvents events = new GattEvents();
        BluetoothGatt gatt = device.connectGatt(context, false, events, BluetoothDevice.TRANSPORT_LE);
        if (gatt == null) throw new ProbeFailure("connect_rejected");
        try {
            events.await("connected");
            if (!gatt.discoverServices()) throw new ProbeFailure("discovery_rejected");
            events.await("services");
            BluetoothGattService service = gatt.getService(SERVICE);
            BluetoothGattCharacteristic value = service == null ? null : service.getCharacteristic(VALUE);
            if (value == null) throw new ProbeFailure("echo_characteristic_missing");
            measure(gatt, value, events, count, result);
        } finally {
            gatt.close();
        }
    }

    @SuppressWarnings("deprecation")
    private void measure(BluetoothGatt gatt, BluetoothGattCharacteristic value, GattEvents events,
                         int count, Bundle result) throws Exception {
        long nonce = SystemClock.elapsedRealtimeNanos();
        long[] elapsed = new long[count];
        int attempted = 0;
        int matched = 0;
        result.putInt("requested", count);
        value.setWriteType(BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT);
        try {
            for (int sequence = 1; sequence <= count; sequence++) {
                byte[] packet = ByteBuffer.allocate(12).putLong(nonce).putInt(sequence).array();
                long start = SystemClock.elapsedRealtimeNanos();
                attempted++;
                if (Build.VERSION.SDK_INT >= 33) {
                    int status = gatt.writeCharacteristic(value, packet,
                            BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT);
                    if (status != BluetoothStatusCodes.SUCCESS) throw new ProbeFailure("write_rejected_" + status);
                } else {
                    value.setValue(packet);
                    if (!gatt.writeCharacteristic(value)) throw new ProbeFailure("write_rejected");
                }
                events.await("write");
                if (!gatt.readCharacteristic(value)) throw new ProbeFailure("read_rejected");
                byte[] echo = events.await("read").value;
                if (Arrays.equals(packet, echo)) {
                    elapsed[matched++] = (SystemClock.elapsedRealtimeNanos() - start) / 1000;
                }
            }
        } finally {
            result.putInt("attempted", attempted);
            result.putInt("matched", matched);
            result.putBoolean("complete", attempted == count && events.completedReads == count);
            if (matched > 0) {
                Arrays.sort(elapsed, 0, matched);
                result.putLong("round_trip_p50_us", elapsed[(matched - 1) / 2]);
                result.putLong("round_trip_p95_us", elapsed[(int) Math.ceil(matched * 0.95) - 1]);
            }
        }
    }

    private static final class GattEvents extends BluetoothGattCallback {
        private final BlockingQueue<Event> queue = new ArrayBlockingQueue<>(8);
        private int completedReads;

        private void record(String step, int status, byte[] value) {
            queue.offer(new Event(step, status, value == null ? null : value.clone()));
        }

        Event await(String expected) throws Exception {
            Event event = queue.poll(5, TimeUnit.SECONDS);
            if (event == null) throw new ProbeFailure(expected + "_timeout");
            if (!expected.equals(event.step) || event.status != BluetoothGatt.GATT_SUCCESS)
                throw new ProbeFailure(expected + "_failed_" + event.step + "_" + event.status);
            if ("read".equals(expected)) completedReads++;
            return event;
        }

        @Override public void onConnectionStateChange(BluetoothGatt gatt, int status, int state) {
            record(state == BluetoothProfile.STATE_CONNECTED ? "connected" : "disconnected", status, null);
        }
        @Override public void onServicesDiscovered(BluetoothGatt gatt, int status) {
            record("services", status, null);
        }
        @Override public void onCharacteristicWrite(BluetoothGatt gatt, BluetoothGattCharacteristic c, int status) {
            if (VALUE.equals(c.getUuid())) record("write", status, null);
        }
        @Override public void onCharacteristicRead(BluetoothGatt gatt, BluetoothGattCharacteristic c, int status) {
            if (Build.VERSION.SDK_INT < 33 && VALUE.equals(c.getUuid())) record("read", status, c.getValue());
        }
        @Override public void onCharacteristicRead(BluetoothGatt gatt, BluetoothGattCharacteristic c,
                                                   byte[] value, int status) {
            if (VALUE.equals(c.getUuid())) record("read", status, value);
        }
    }

    private static final class Event {
        final String step;
        final int status;
        final byte[] value;
        Event(String step, int status, byte[] value) {
            this.step = step;
            this.status = status;
            this.value = value;
        }
    }

    private static final class ProbeFailure extends Exception {
        ProbeFailure(String reason) { super(reason); }
    }
}
