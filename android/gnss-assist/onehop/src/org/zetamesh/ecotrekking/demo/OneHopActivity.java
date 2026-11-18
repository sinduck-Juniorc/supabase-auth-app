package org.zetamesh.ecotrekking.demo;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.*;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.*;
import android.view.Gravity;
import android.widget.*;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Collections;

public final class OneHopActivity extends Activity {
    private static final int COMPANY = 0xffff;
    private static final int EXPORT = 2;
    private static final int EXPORT_AND_EXIT = 3;
    private final Handler ui = new Handler(Looper.getMainLooper());
    private TextView digit, status, logStatus;
    private Button start, export, saveAndExit;
    private OneHopLog log;
    private OneHopLog.Session session;
    private BluetoothLeScanner scanner;
    private BluetoothLeAdvertiser advertiser;
    private ScanCallback scan;
    private AdvertiseCallback beacon;
    private int boot = -1, lastSequence;
    private long lastArrival;
    private final Runnable expire = () -> {
        record("display_expired", "sender_boot_id", boot, "sequence", lastSequence);
        digit.setText("—");
        status.setText("데이터 만료 · 다음 입력 대기");
    };

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        log = new OneHopLog(getFilesDir());
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setGravity(Gravity.CENTER);
        digit = new TextView(this);
        digit.setTextSize(100);
        digit.setText("—");
        status = new TextView(this);
        status.setText("EcoOneHop 스케치를 사용하는 R4용");
        start = new Button(this);
        start.setText("1홉 수신 시작");
        start.setOnClickListener(v -> authorize());
        logStatus = new TextView(this);
        logStatus.setText("수신 로그는 앱에 자동 저장됩니다.");
        export = new Button(this);
        export.setText("로그 내보내기");
        export.setOnClickListener(v -> chooseFile(EXPORT));
        saveAndExit = new Button(this);
        saveAndExit.setText("저장 후 종료");
        saveAndExit.setOnClickListener(v -> chooseFile(EXPORT_AND_EXIT));
        layout.addView(digit);
        layout.addView(status);
        layout.addView(start);
        layout.addView(logStatus);
        layout.addView(export);
        layout.addView(saveAndExit);
        setContentView(layout);
        enableExport();
    }

    private void authorize() {
        String[] required = Build.VERSION.SDK_INT >= 31
                ? new String[]{Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_CONNECT,
                    Manifest.permission.BLUETOOTH_ADVERTISE}
                : new String[]{Manifest.permission.ACCESS_FINE_LOCATION};
        for (String permission : required) {
            if (checkSelfPermission(permission) != PackageManager.PERMISSION_GRANTED) {
                requestPermissions(required, 1);
                return;
            }
        }
        begin();
    }

    @Override public void onRequestPermissionsResult(int code, String[] names, int[] grants) {
        super.onRequestPermissionsResult(code, names, grants);
        if (code != 1 || grants.length == 0) return;
        for (int grant : grants) if (grant != PackageManager.PERMISSION_GRANTED) {
            status.setText("근처 기기 권한을 확인하세요.");
            return;
        }
        begin();
    }

    private void begin() {
        session = new OneHopLog.Session();
        record("session_start", "app_version", "0.2.0", "protocol", "eco_one_hop_digit_v1");
        try {
            BluetoothManager manager = getSystemService(BluetoothManager.class);
            BluetoothAdapter adapter = manager == null ? null : manager.getAdapter();
            scanner = adapter == null ? null : adapter.getBluetoothLeScanner();
            advertiser = adapter == null ? null : adapter.getBluetoothLeAdvertiser();
            if (scanner == null || advertiser == null) {
                stop("Bluetooth 스캔·광고 지원 및 켜짐 상태를 확인하세요.", "bluetooth_unavailable");
                return;
            }
            start.setEnabled(false);
            status.setText("광고 시작 중…");
            scan = new ScanCallback() {
                @Override public void onScanResult(int type, ScanResult result) {
                    if (scan != this || result.getScanRecord() == null) return;
                    accept(result);
                }
                @Override public void onScanFailed(int error) {
                    if (scan == this) {
                        record("scan_error", "code", error);
                        stop("스캔 실패 " + error, "scan_error");
                    }
                }
            };
            beacon = new AdvertiseCallback() {
                @Override public void onStartSuccess(AdvertiseSettings settings) {
                    if (beacon == this) {
                        record("presence_advertising_started");
                        if (boot == -1) status.setText("R4에서 0 또는 1을 보내세요.");
                    }
                }
                @Override public void onStartFailure(int error) {
                    if (beacon == this) {
                        record("advertising_error", "code", error);
                        stop("존재 광고 실패 " + error, "advertising_error");
                    }
                }
            };
            ScanFilter filter = new ScanFilter.Builder().setManufacturerData(COMPANY,
                    new byte[]{'Z','M',1,2,1}).build();
            scanner.startScan(Collections.singletonList(filter), new ScanSettings.Builder()
                    .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).build(), scan);
            advertiser.startAdvertising(new AdvertiseSettings.Builder().setConnectable(false)
                    .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_BALANCED).build(),
                    new AdvertiseData.Builder().addManufacturerData(COMPANY, new byte[]{'Z','M',1,3,2}).build(),
                    beacon);
        } catch (SecurityException | IllegalStateException e) {
            stop("Bluetooth 권한 및 켜짐 상태를 확인하세요.", "bluetooth_setup_error");
        }
    }

    private void accept(ScanResult result) {
        OneHopFrame frame = OneHopFrame.parse(result.getScanRecord().getManufacturerSpecificData(COMPANY));
        if (frame == null) {
            session.invalid++;
            return;
        }
        long arrival = result.getTimestampNanos() / 1000000L;
        long remaining = frame.remainingMs - (SystemClock.elapsedRealtime() - arrival);
        if (remaining <= 0) {
            session.expired++;
            return;
        }
        if (arrival < lastArrival ||
                (frame.boot == boot && !OneHopFrame.newer(lastSequence, frame.sequence))) {
            session.repeatedOrOlder++;
            return;
        }
        lastArrival = arrival;
        boot = frame.boot;
        lastSequence = frame.sequence;
        session.received++;
        record("packet_received", "digit", frame.digit, "sequence", frame.sequence,
                "sender_boot_id", frame.boot, "rssi_dbm", result.getRssi(),
                "received_elapsed_ms", arrival, "remaining_ttl_ms", remaining);
        digit.setText(Integer.toString(frame.digit));
        status.setText("R4 → 폰 · 1홉 · 순번 " + frame.sequence);
        ui.removeCallbacks(expire);
        ui.postDelayed(expire, remaining);
    }

    private void stop(String message, String reason) {
        ScanCallback activeScan = scan;
        AdvertiseCallback activeBeacon = beacon;
        scan = null;
        beacon = null;
        try { if (activeScan != null) scanner.stopScan(activeScan); }
        catch (SecurityException | IllegalStateException ignored) { }
        try { if (activeBeacon != null) advertiser.stopAdvertising(activeBeacon); }
        catch (SecurityException | IllegalStateException ignored) { }
        ui.removeCallbacks(expire);
        if (session != null) {
            record("session_end", "reason", reason, "received_count", session.received,
                    "invalid_count", session.invalid, "expired_count", session.expired,
                    "repeated_or_older_count", session.repeatedOrOlder);
            session = null;
        }
        boot = -1;
        lastArrival = 0;
        digit.setText("—");
        status.setText(message);
        start.setEnabled(true);
    }

    private void record(String event, Object... fields) {
        if (session == null) return;
        try {
            log.append(session, SystemClock.elapsedRealtime(), event, fields);
            enableExport();
        } catch (IOException error) {
            logStatus.setText("로그 저장에 실패했습니다. 기기 저장 공간을 확인하세요.");
        }
    }

    private void enableExport() {
        export.setEnabled(log.hasRecords());
        saveAndExit.setEnabled(log.hasRecords());
    }

    private void chooseFile(int request) {
        stop("1홉 수신이 종료됐습니다.", request == EXPORT_AND_EXIT ? "save_and_exit" : "export");
        Intent picker = new Intent(Intent.ACTION_CREATE_DOCUMENT);
        picker.addCategory(Intent.CATEGORY_OPENABLE);
        picker.setType("application/octet-stream");
        picker.putExtra(Intent.EXTRA_TITLE, "eco-trekking-one-hop-" + System.currentTimeMillis() + ".jsonl");
        try {
            startActivityForResult(picker, request);
        } catch (android.content.ActivityNotFoundException error) {
            logStatus.setText("파일 저장 위치를 열 수 없습니다.");
        }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != EXPORT && request != EXPORT_AND_EXIT) return;
        Uri destination = data == null ? null : data.getData();
        if (result != RESULT_OK || destination == null) {
            logStatus.setText("파일 내보내기를 취소했습니다.");
            return;
        }
        start.setEnabled(false);
        export.setEnabled(false);
        saveAndExit.setEnabled(false);
        logStatus.setText("파일 저장 중…");
        new Thread(() -> writeExport(destination, request == EXPORT_AND_EXIT), "one-hop-log-export").start();
    }

    private void writeExport(Uri destination, boolean exitAfter) {
        boolean saved;
        try (OutputStream out = getContentResolver().openOutputStream(destination, "wt")) {
            if (out == null) throw new IOException("No output stream");
            log.export(out);
            saved = true;
        } catch (IOException | SecurityException error) {
            saved = false;
        }
        boolean success = saved;
        runOnUiThread(() -> {
            if (isDestroyed()) return;
            start.setEnabled(true);
            enableExport();
            logStatus.setText(success ? "로그 파일을 저장했습니다." : "파일 저장에 실패했습니다. 다시 시도하세요.");
            if (success && exitAfter) finishAndRemoveTask();
        });
    }

    @Override protected void onStop() {
        if (session != null) stop("1홉 수신이 종료됐습니다.", "screen_closed");
        super.onStop();
    }
}
