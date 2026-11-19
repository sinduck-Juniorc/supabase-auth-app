package org.zetamesh.gnss.v3.relay;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.*;
import android.bluetooth.le.*;
import android.content.pm.PackageManager;
import android.os.*;
import android.view.WindowManager;
import android.widget.*;
import java.security.SecureRandom;
import java.util.Arrays;
import java.util.Collections;

public final class RelayActivity extends Activity {
    private static final long FRESH = 5000, BURST = 1500;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private final int relay = new SecureRandom().nextInt();
    private TextView status;
    private Button start;
    private BluetoothLeScanner scanner;
    private BluetoothLeAdvertiser advertiser;
    private AdvertiseCallback publishing;
    private ScanCallback listening;
    private byte[] current, outgoing;
    private long lastSink, burstEnd;
    private int sinkBoot, beaconSeq, rssi, source, sequence, forwarded;
    private double reception;
    private boolean seenSink, seenData;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = (int)(24 * getResources().getDisplayMetrics().density);
        layout.setPadding(pad, pad, pad, pad);
        status = new TextView(this);
        status.setTextSize(20);
        status.setText("R4와 노트북 사이에서 중계할 준비가 되었습니다.");
        start = new Button(this);
        start.setText("중계 시작");
        start.setOnClickListener(v -> authorize());
        layout.addView(status); layout.addView(start); setContentView(layout);
    }
    private void authorize() {
        String[] permissions = Build.VERSION.SDK_INT >= 31 ?
            new String[]{Manifest.permission.BLUETOOTH_ADVERTISE, Manifest.permission.BLUETOOTH_SCAN,
                    Manifest.permission.BLUETOOTH_CONNECT} : new String[]{Manifest.permission.ACCESS_FINE_LOCATION};
        for (String p : permissions) if (checkSelfPermission(p) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(permissions, 1); return;
        }
        begin();
    }
    @Override public void onRequestPermissionsResult(int code, String[] names, int[] grants) {
        super.onRequestPermissionsResult(code, names, grants);
        if (code != 1 || grants.length == 0) return;
        for (int grant : grants) if (grant != PackageManager.PERMISSION_GRANTED) {
            status.setText("Bluetooth 권한이 필요합니다."); return;
        }
        begin();
    }
    private void begin() {
        if (listening != null) return;
        try {
            BluetoothManager manager = getSystemService(BluetoothManager.class);
            BluetoothAdapter adapter = manager == null ? null : manager.getAdapter();
            scanner = adapter == null ? null : adapter.getBluetoothLeScanner();
            advertiser = adapter == null ? null : adapter.getBluetoothLeAdvertiser();
            if (scanner == null || advertiser == null) { stop("Bluetooth 스캔·광고 지원과 켜짐 상태를 확인하세요."); return; }
            listening = new ScanCallback() {
                @Override public void onScanFailed(int error) {
                    if (listening == this) stop("스캔 실패 " + error);
                }
                @Override public void onScanResult(int type, ScanResult result) {
                    if (listening != this || result.getScanRecord() == null) return;
                    long at = result.getTimestampNanos() / 1000000L;
                    if (SystemClock.elapsedRealtime() - at > 1000) return;
                    observe(result.getScanRecord().getManufacturerSpecificData(RelayWire.COMPANY), result.getRssi(), at);
                }
            };
            ScanFilter filter = new ScanFilter.Builder().setManufacturerData(RelayWire.COMPANY, new byte[]{'Z','R',1}).build();
            scanner.startScan(Collections.singletonList(filter), new ScanSettings.Builder()
                    .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build(), listening);
            start.setEnabled(false);
            tick.run();
        } catch (RuntimeException e) { stop("BLE 시작 실패 · " + e.getClass().getSimpleName()); }
    }
    private void observe(byte[] data, int strength, long at) {
        if (RelayWire.is(data, 1, 8)) {
            int boot = RelayWire.u16(data, 4), seq = RelayWire.u16(data, 6);
            int gap = (seq - beaconSeq) & 65535;
            if (!seenSink || boot != sinkBoot || at - lastSink >= FRESH) reception = .1;
            else {
                if (gap == 0 || gap >= 32768) return;
                reception = .75 * reception + .25 / gap;
            }
            seenSink = true; sinkBoot = boot; beaconSeq = seq;
            lastSink = at; rssi = Math.max(-127, Math.min(0, strength));
            return;
        }
        if (!seenSink || at - lastSink >= FRESH) return;
        byte[] next = RelayWire.forward(data, relay);
        if (next == null) return;
        int origin = RelayWire.i32(next, 8), seq = RelayWire.i32(next, 12);
        if (seenData && origin == source && seq - sequence <= 0) return;
        seenData = true; source = origin; sequence = seq;
        outgoing = next; burstEnd = SystemClock.elapsedRealtime() + BURST;
        refresh();
    }
    private final Runnable tick = new Runnable() {
        @Override public void run() {
            if (listening == null) return;
            refresh();
            if (listening != null) ui.postDelayed(this, 250);
        }
    };
    private void refresh() {
        long now = SystemClock.elapsedRealtime();
        byte[] next = null;
        if (outgoing != null && now < burstEnd) next = outgoing;
        else if (seenSink && now - lastSink < FRESH) {
            int battery = getSystemService(BatteryManager.class).getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);
            next = RelayWire.offer(relay, battery < 0 || battery > 100 ? 255 : battery, rssi,
                    (int)Math.round(reception * 100), (int)((now-lastSink) / 1000));
        }
        if (Arrays.equals(next, current)) {
            if (next == null) status.setText("R4 탐색 중 · 중계 광고 " + forwarded + "건");
            return;
        }
        try {
            stopAd();
            if (next == null) return;
            current = next;
            final boolean forwarding = next[3] == 4;
            publishing = new AdvertiseCallback() {
                @Override public void onStartSuccess(AdvertiseSettings settings) {
                    if (publishing != this) return;
                    if (forwarding) ++forwarded;
                    status.setText((forwarding ? "중계 광고 시작 · 값 " + current[16] + " · 순번 " +
                            Integer.toUnsignedString(sequence) : "R4 발견 · 노트북의 선택 대기") + "\n중계 광고 " + forwarded + "건");
                }
                @Override public void onStartFailure(int error) {
                    if (publishing == this) stop("광고 실패 " + error);
                }
            };
            advertiser.startAdvertising(new AdvertiseSettings.Builder().setConnectable(false)
                    .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY).build(),
                    new AdvertiseData.Builder().addManufacturerData(RelayWire.COMPANY, next).build(), publishing);
        } catch (RuntimeException e) { stop("BLE 광고 오류 · " + e.getClass().getSimpleName()); }
    }
    private void stopAd() {
        AdvertiseCallback old = publishing;
        publishing = null; current = null;
        if (old != null) advertiser.stopAdvertising(old);
    }
    private void stop(String message) {
        ui.removeCallbacks(tick);
        ScanCallback old = listening; listening = null;
        try { if (old != null) scanner.stopScan(old); } catch (RuntimeException ignored) {}
        try { stopAd(); } catch (RuntimeException ignored) {}
        outgoing = null; seenData = seenSink = false; forwarded = 0;
        start.setEnabled(true); status.setText(message);
    }
    @Override public void onStop() { stop("중계를 시작하면 R4를 탐색합니다."); super.onStop(); }
}
