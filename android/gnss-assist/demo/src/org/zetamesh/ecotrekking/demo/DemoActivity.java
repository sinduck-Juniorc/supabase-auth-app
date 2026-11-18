package org.zetamesh.ecotrekking.demo;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothGatt;
import android.bluetooth.BluetoothGattCallback;
import android.bluetooth.BluetoothGattCharacteristic;
import android.bluetooth.BluetoothGattDescriptor;
import android.bluetooth.BluetoothGattService;
import android.bluetooth.BluetoothManager;
import android.bluetooth.BluetoothProfile;
import android.bluetooth.BluetoothStatusCodes;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanFilter;
import android.bluetooth.le.ScanResult;
import android.bluetooth.le.ScanSettings;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelUuid;
import android.view.Gravity;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

import java.util.Collections;
import java.util.UUID;

public final class DemoActivity extends Activity {
    private static final UUID SERVICE = UUID.fromString("cdc62460-724d-4ace-ad2b-ac71c8371fd1");
    private static final UUID DIGIT = UUID.fromString("cdc62461-724d-4ace-ad2b-ac71c8371fd1");
    private static final UUID NOTIFY = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb");
    private static final int PERMISSIONS = 1;

    private final Handler ui = new Handler(Looper.getMainLooper());
    private final Runnable timeout = () -> reset("시간 초과 · R4를 켜고 다시 연결하세요.");
    private BluetoothLeScanner scanner;
    private ScanCallback scan;
    private BluetoothGatt gatt;
    private TextView status;
    private TextView digit;
    private Button connect;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        layout.setBackgroundColor(Color.rgb(243, 247, 245));
        int padding = Math.round(24 * getResources().getDisplayMetrics().density);
        layout.setPadding(padding, padding, padding, padding);
        digit = label("—", 104);
        digit.setContentDescription("수신값 없음");
        status = label("R4에 연결하세요.", 18);
        connect = new Button(this);
        connect.setText("R4 연결");
        connect.setOnClickListener(view -> requestConnection());
        layout.addView(digit);
        layout.addView(status);
        layout.addView(connect);
        setContentView(layout);
    }

    private TextView label(String text, int sp) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(sp);
        view.setTextColor(Color.rgb(20, 53, 44));
        view.setGravity(Gravity.CENTER);
        return view;
    }

    private void requestConnection() {
        String[] required = Build.VERSION.SDK_INT >= 31
                ? new String[]{Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT}
                : new String[]{Manifest.permission.ACCESS_FINE_LOCATION};
        for (String permission : required) {
            if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(required, PERMISSIONS);
                return;
            }
        }
        startScan();
    }

    @Override public void onRequestPermissionsResult(int request, String[] permissions, int[] grants) {
        super.onRequestPermissionsResult(request, permissions, grants);
        if (request != PERMISSIONS) return;
        if (grants.length == 0) return;
        for (int grant : grants) {
            if (grant != PackageManager.PERMISSION_GRANTED) {
                status.setText("R4 연결에 필요한 Bluetooth 권한을 허용하세요.");
                return;
            }
        }
        startScan();
    }

    private void startScan() {
        try {
            BluetoothManager manager = getSystemService(BluetoothManager.class);
            BluetoothAdapter adapter = manager == null ? null : manager.getAdapter();
            scanner = adapter == null ? null : adapter.getBluetoothLeScanner();
            if (scanner == null) {
                reset("Bluetooth를 켠 뒤 다시 연결하세요.");
                return;
            }
            connect.setEnabled(false);
            status.setText("R4 찾는 중…");
            scan = new ScanCallback() {
                @Override public void onScanResult(int type, ScanResult found) {
                    ui.post(() -> {
                        if (scan == this) connectTo(found.getDevice());
                    });
                }

                @Override public void onScanFailed(int error) {
                    ui.post(() -> {
                        if (scan == this) reset("Bluetooth 검색 오류 (" + error + ")");
                    });
                }
            };
            ScanFilter filter = new ScanFilter.Builder().setServiceUuid(new ParcelUuid(SERVICE)).build();
            ScanSettings settings = new ScanSettings.Builder().setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build();
            scanner.startScan(Collections.singletonList(filter), settings, scan);
            ui.postDelayed(timeout, 12_000);
        } catch (SecurityException error) {
            reset("Bluetooth 권한을 확인하세요.");
        }
    }

    private void connectTo(BluetoothDevice device) {
        stopScan();
        ui.removeCallbacks(timeout);
        status.setText("R4 연결 중…");
        try {
            gatt = device.connectGatt(this, false, events, BluetoothDevice.TRANSPORT_LE);
            if (gatt == null) reset("R4 연결을 시작할 수 없습니다.");
            else ui.postDelayed(timeout, 12_000);
        } catch (SecurityException error) {
            reset("Bluetooth 권한을 확인하세요.");
        }
    }

    private final BluetoothGattCallback events = new BluetoothGattCallback() {
        @Override public void onConnectionStateChange(BluetoothGatt peer, int code, int state) {
            ui.post(() -> {
                if (peer != gatt) return;
                if (code != BluetoothGatt.GATT_SUCCESS || state == BluetoothProfile.STATE_DISCONNECTED) {
                    reset("R4 연결이 끊겼습니다. 다시 연결하세요.");
                } else if (state == BluetoothProfile.STATE_CONNECTED) {
                    try {
                        if (!peer.discoverServices()) reset("R4 서비스를 검색할 수 없습니다.");
                    } catch (SecurityException error) {
                        reset("Bluetooth 권한을 확인하세요.");
                    }
                }
            });
        }

        @Override public void onServicesDiscovered(BluetoothGatt peer, int code) {
            ui.post(() -> {
                if (peer == gatt) subscribe(peer, code);
            });
        }

        @Override public void onDescriptorWrite(BluetoothGatt peer, BluetoothGattDescriptor descriptor, int code) {
            ui.post(() -> {
                if (peer != gatt || !NOTIFY.equals(descriptor.getUuid())) return;
                if (code == BluetoothGatt.GATT_SUCCESS) {
                    ui.removeCallbacks(timeout);
                    status.setText("R4 연결됨 · 시리얼 모니터에서 0 또는 1을 보내세요.");
                } else {
                    reset("R4 알림 구독에 실패했습니다.");
                }
            });
        }

        @Override public void onCharacteristicChanged(BluetoothGatt peer, BluetoothGattCharacteristic value,
                                                      byte[] bytes) {
            receive(peer, value, bytes);
        }

        @SuppressWarnings("deprecation")
        @Override public void onCharacteristicChanged(BluetoothGatt peer, BluetoothGattCharacteristic value) {
            if (Build.VERSION.SDK_INT < 33) receive(peer, value, value.getValue());
        }
    };

    @SuppressWarnings("deprecation")
    private void subscribe(BluetoothGatt peer, int code) {
        BluetoothGattService service = peer.getService(SERVICE);
        BluetoothGattCharacteristic value = service == null ? null : service.getCharacteristic(DIGIT);
        BluetoothGattDescriptor descriptor = value == null ? null : value.getDescriptor(NOTIFY);
        if (code != BluetoothGatt.GATT_SUCCESS || descriptor == null) {
            reset("R4 시연 스케치의 서비스를 찾을 수 없습니다.");
            return;
        }
        try {
            if (!peer.setCharacteristicNotification(value, true)) {
                reset("R4 알림을 켤 수 없습니다.");
                return;
            }
            byte[] enable = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE;
            boolean submitted;
            if (Build.VERSION.SDK_INT >= 33) {
                submitted = peer.writeDescriptor(descriptor, enable) == BluetoothStatusCodes.SUCCESS;
            } else {
                descriptor.setValue(enable);
                submitted = peer.writeDescriptor(descriptor);
            }
            if (!submitted) reset("R4 알림 구독을 시작할 수 없습니다.");
        } catch (SecurityException error) {
            reset("Bluetooth 권한을 확인하세요.");
        }
    }

    private void receive(BluetoothGatt peer, BluetoothGattCharacteristic value, byte[] bytes) {
        if (!DIGIT.equals(value.getUuid()) || bytes == null || bytes.length != 1) return;
        int number = bytes[0];
        if (number != 0 && number != 1) return;
        ui.post(() -> {
            if (peer != gatt) return;
            digit.setText(Integer.toString(number));
            digit.setContentDescription("수신값 " + number);
        });
    }

    private void stopScan() {
        ScanCallback active = scan;
        scan = null;
        if (active != null && scanner != null) {
            try { scanner.stopScan(active); }
            catch (SecurityException ignored) { }
        }
        scanner = null;
    }

    private void reset(String message) {
        ui.removeCallbacks(timeout);
        stopScan();
        BluetoothGatt peer = gatt;
        gatt = null;
        if (peer != null) {
            try { peer.close(); }
            catch (SecurityException ignored) { }
        }
        status.setText(message);
        digit.setText("—");
        digit.setContentDescription("수신값 없음");
        connect.setEnabled(true);
    }

    @Override protected void onStop() {
        reset("R4에 연결하세요.");
        super.onStop();
    }
}
