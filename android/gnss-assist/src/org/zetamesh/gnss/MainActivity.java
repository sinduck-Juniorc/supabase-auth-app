package org.zetamesh.gnss;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.*;
import android.net.*;
import android.os.*;
import android.provider.Settings;
import android.view.*;
import android.widget.*;
import org.json.JSONObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.concurrent.*;

public class MainActivity extends Activity {
    private final Handler handler = new Handler(Looper.getMainLooper());
    private LocationManager manager;
    private TextView status, details;
    private LinearLayout body;
    private Trial trial;
    private GnssStatus.Callback callback;
    private LocationListener gps, network;
    private Runnable timeout;
    private boolean exporting = false;
    private String trialId = "";
    private int used = 0;
    private File events;
    private volatile boolean logFailed;
    private final ExecutorService io = new ThreadPoolExecutor(1,1,0L,TimeUnit.MILLISECONDS,
        new ArrayBlockingQueue<Runnable>(128));
    private final ExecutorService aiding = Executors.newSingleThreadExecutor();
    private final Runnable cleanupRetry = () -> cleanup();
    private static final long LOG_LIMIT = 8L * 1024 * 1024;
    private void writeTask(Runnable task) {
        try { io.execute(task); } catch (RejectedExecutionException e) { logFailure(); }
    }
    private void logFailure() {
        logFailed=true;
        handler.post(() -> { stopTrial("log_limit_or_write_error");
            status.setText("로그 기록 중단: 저장공간 또는 8MiB 한도. 로그를 내보낸 뒤 앱 저장공간을 정리하세요."); });
    }
    private boolean expired(Trial current) {
        if (SystemClock.elapsedRealtimeNanos()-current.startedNanos >= 120000000000L) {
            stopTrial("timeout"); return true;
        }
        return false;
    }
    private boolean cleanup() {
        Cleanup.run(
            () -> { if(gps!=null) { manager.removeUpdates(gps); gps=null; } },
            () -> { if(network!=null) { manager.removeUpdates(network); network=null; } },
            () -> { if(callback!=null) { manager.unregisterGnssStatusCallback(callback); callback=null; } });
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        return gps==null && network==null && callback==null;
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        manager = (LocationManager)getSystemService(LOCATION_SERVICE);
        events = new File(getFilesDir(), "gnss-events.jsonl");
        ScrollView scroll = new ScrollView(this);
        body = new LinearLayout(this); body.setOrientation(LinearLayout.VERTICAL); body.setPadding(28,24,28,24);
        scroll.addView(body); setContentView(scroll);
        scroll.setOnApplyWindowInsetsListener((v, insets) -> {
            android.graphics.Insets bars = insets.getInsets(WindowInsets.Type.systemBars());
            v.setPadding(bars.left,bars.top,bars.right,bars.bottom); return insets;
        });
        text("ZetaMesh · 내장 GNSS 진단",24);
        text("진단 대상: S26+ 한국 모델 / Android 17 · One UI 9 (실기기 미검증)\n실제 단말: " + Build.MODEL + " / Android " + Build.VERSION.RELEASE,15);
        text("기본 측정과 보조정보 갱신 요청을 비교합니다. 요청 반환값은 주입 성공 증거가 아닙니다. R4 좌표 주입 및 속도 개선은 아직 검증되지 않았습니다.",16);
        button("정확한 위치 권한 허용", () -> requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION},1));
        button("휴대폰 위치 설정 열기", () -> startActivity(new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS)));
        button("A · 기본 GNSS 측정 (120초 종료 예정)", () -> startTrial("baseline"));
        button("B · 시간·PSDS 갱신 요청 후 측정", () -> startTrial("assisted"));
        button("C · B + 네트워크 위치 요청 (별도 비교)", () -> startTrial("assisted_network"));
        button("측정 중단", () -> stopTrial("user_stop"));
        button("실제 로그 내보내기", this::export);
        status = text("대기 중 · GPS 모듈 구매 없이 시험 가능",18);
        details = text("옥외의 같은 위치에서 다른 지도 앱을 종료하고 시험하세요. 모의 위치 앱은 해제하세요. 로그는 단말 내부에만 저장되며 좌표는 기록하지 않습니다.",15);
        event("app_open", obj("model",Build.MODEL,"android",Build.VERSION.RELEASE,"sdk",Build.VERSION.SDK_INT,"fingerprint",Build.FINGERPRINT,"app_version","0.1.1"));
    }
    private TextView text(String value,int size) {
        TextView v=new TextView(this);v.setText(value);v.setTextSize(size);v.setPadding(0,10,0,10);body.addView(v);return v;
    }
    private void button(String title,Runnable action) { Button b=new Button(this);b.setText(title);body.addView(b);b.setOnClickListener(v->action.run()); }
    private JSONObject obj(Object... values) {
        JSONObject o=new JSONObject(); try { for(int i=0;i<values.length;i+=2) o.put((String)values[i],values[i+1]==null?JSONObject.NULL:values[i+1]); } catch(Exception e) { throw new IllegalStateException(e); } return o;
    }
    private void event(String name,JSONObject data) {
        try {
            data.put("event",name); data.put("trial_id",trialId); data.put("wall_utc_ms",System.currentTimeMillis()); data.put("elapsed_ms",SystemClock.elapsedRealtime());
            final byte[] bytes=(data.toString()+"\n").getBytes(StandardCharsets.UTF_8);
            writeTask(() -> {
                try {
                    if(events.length()+bytes.length>LOG_LIMIT) { logFailure(); return; }
                    try(FileOutputStream out=new FileOutputStream(events,true)) {out.write(bytes);}
                } catch(Exception e) {logFailure();}
            });
        } catch(Exception e) {logFailure();}
    }

    private boolean fine() { return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED; }
    private void startTrial(String mode) {
        if(trial!=null && trial.active) { status.setText("현재 측정을 먼저 종료하세요.");return; }
        if(exporting) return;
        handler.removeCallbacks(cleanupRetry);
        if(!cleanup()) { status.setText("이전 위치 수신 해제 실패: 새 측정을 차단합니다. 앱을 강제 종료하세요."); return; }
        if(events.length()>=LOG_LIMIT) {status.setText("로그 한도 도달: 내보낸 뒤 앱 저장공간을 정리하세요.");return;}
        if(!fine()) { status.setText("정확한 위치 권한이 필요합니다. 권한 허용 후 다시 누르세요.");return; }
        if(!manager.isLocationEnabled() || !manager.isProviderEnabled(LocationManager.GPS_PROVIDER)) { status.setText("휴대폰 위치 기능을 켜세요.");return; }
        trialId=UUID.randomUUID().toString(); trial=new Trial(mode,SystemClock.elapsedRealtimeNanos()); used=0;logFailed=false;
        final Trial current=trial;
        ConnectivityManager cm=(ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
        NetworkCapabilities nc=cm.getNetworkCapabilities(cm.getActiveNetwork());
        event("trial_start",obj("mode",mode,"timeout_ms",120000,"model",Build.MODEL,"android",Build.VERSION.RELEASE,"sdk",Build.VERSION.SDK_INT,"fingerprint",Build.FINGERPRINT,"network_validated",nc!=null&&nc.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED),"power_save",((PowerManager)getSystemService(POWER_SERVICE)).isPowerSaveMode()));
        callback=new GnssStatus.Callback() {
            @Override public void onStarted() { if(current!=trial||!current.active||expired(current))return;current.engineStarted=true;event("gnss_started",obj()); }
            @Override public void onStopped() { if(current!=trial||!current.active||expired(current))return;event("gnss_stopped",obj()); }
            @Override public void onFirstFix(int ttff) {
                if(current!=trial||!current.active||expired(current))return;
                if(current.firstFix(ttff,SystemClock.elapsedRealtimeNanos())) { event("gnss_first_fix",obj("ttff_ms",ttff));refresh();finishIfReady(); }
                else event("first_fix_excluded",obj("ttff_ms",ttff,"reason","no_started_event_or_duplicate"));
            }
            @Override public void onSatelliteStatusChanged(GnssStatus s) {
                if(current!=trial||!current.active||expired(current))return;
                used=0;for(int i=0;i<s.getSatelliteCount();i++)if(s.usedInFix(i))used++;
                details.setText("보이는 위성 " + s.getSatelliteCount() + " · 측위 사용 " + used + "\n현재 시도 " + current.mode + "\n엔진 시작 콜백 " + current.engineStarted);
            }
        };
        gps=new LocationListener() {
            @Override public void onLocationChanged(Location l) {
                if(current!=trial||!current.active||expired(current))return;
                boolean mock=l.isFromMockProvider();
                if(!LocationManager.GPS_PROVIDER.equals(l.getProvider()))return;
                if(!current.location(l.getElapsedRealtimeNanos(),SystemClock.elapsedRealtimeNanos(),mock)) {
                    event("gps_fix_excluded",obj("mock",mock,"reason","mock_stale_or_future"));
                    if(mock)stopTrial("mock_detected"); return;
                }
                event("gps_location",obj("request_to_fix_ms",current.firstGpsMs,"accuracy_m",l.hasAccuracy()?l.getAccuracy():null,"used_satellites",used,"provider",l.getProvider(),"mock",false));
                refresh();finishIfReady();
            }
            @Override public void onProviderDisabled(String provider) { if(current==trial&&current.active)stopTrial("provider_disabled"); }
        };
        try {
            current.callbackRegistered=manager.registerGnssStatusCallback(callback,handler);
            if(!current.callbackRegistered) { stopTrial("callback_registration_failed");return; }
            manager.requestLocationUpdates(LocationManager.GPS_PROVIDER,1000L,0f,gps,Looper.getMainLooper());
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
            timeout=()->{if(current==trial&&current.active)stopTrial("timeout");};handler.postDelayed(timeout,120000);
            if(!mode.equals("baseline")) aiding.execute(() -> {
                if(current.active) command("force_time_injection", current);
                if(current.active) command("force_psds_injection", current);
            });
            if(mode.equals("assisted_network")) networkRequest(current);
            refresh();
        } catch(RuntimeException e) { event("start_error",obj("exception",e.getClass().getSimpleName()));stopTrial("start_error"); }
    }
    private void command(String command, Trial current) {
        try {
            boolean returned=manager.sendExtraCommand(LocationManager.GPS_PROVIDER,command,null);
            handler.post(() -> {if(current==trial)event("aid_request",obj("command",command,"api_return",returned,"injection_confirmed",false));});
        } catch(RuntimeException e) {
            handler.post(() -> {if(current==trial)event("aid_request_error",obj("command",command,"exception",e.getClass().getSimpleName(),"injection_confirmed",false));});
        }
    }
    private void networkRequest(Trial current) {
        if(!manager.isProviderEnabled(LocationManager.NETWORK_PROVIDER)) {event("network_unavailable",obj());return;}
        network=new LocationListener() {
            @Override public void onLocationChanged(Location l) {
                if(current!=trial||!current.active||expired(current))return;
                event("network_location",obj("provider",l.getProvider(),"mock",l.isFromMockProvider(),"age_ms",(SystemClock.elapsedRealtimeNanos()-l.getElapsedRealtimeNanos())/1000000L,"counts_as_gnss_fix",false));
                try { manager.removeUpdates(this); network=null; } catch(RuntimeException e) { stopTrial("network_cleanup_error"); }
            }
        };
        // 실제 시스템 network provider 요청이다. 받은 값을 앱이 GNSS HAL에 직접 주입하지 않는다.
        manager.requestLocationUpdates(LocationManager.NETWORK_PROVIDER,1000L,0f,network,Looper.getMainLooper());
    }
    private void refresh() {
        status.setText("측정 " + trial.mode + "\n엔진 TTFF: " + (trial.engineTtffMs==null?"아직 없음":trial.engineTtffMs+"ms") + "\n요청→새 GPS 좌표: " + (trial.firstGpsMs==null?"아직 없음":trial.firstGpsMs+"ms") + "\n보조정보 실제 주입 여부: 확인 불가");
    }
    private void finishIfReady() { if(trial.comparable())stopTrial("first_fix"); }
    private void stopTrial(String reason) {
        if(trial==null||!trial.active) { cleanup(); return; }
        trial.active=false; if(timeout!=null)handler.removeCallbacks(timeout);
        boolean cleaned=cleanup();
        handler.removeCallbacks(cleanupRetry);
        if(!cleaned) { event("cleanup_error",obj("retry_scheduled",true)); handler.postDelayed(cleanupRetry,1000); }
        getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        boolean valid=reason.equals("first_fix")&&trial.comparable()&&!logFailed&&cleaned;
        event("trial_end",obj("mode",trial.mode,"reason",reason,"engine_ttff_ms",trial.engineTtffMs,"request_to_gps_ms",trial.firstGpsMs,"engine_started_observed",trial.engineStarted,"mock_seen",trial.mockSeen,"log_failed",logFailed,"eligible_first_fix",valid,"engine_session_origin_verified",false,"elapsed_trial_ms",(SystemClock.elapsedRealtimeNanos()-trial.startedNanos)/1000000L));
        status.setText("측정 종료: " + reason + "\n엔진 TTFF: " + trial.engineTtffMs + "ms\n비교에 사용할 첫 측정: " + valid + "\n캐시·다른 앱·시험 순서의 영향은 보고서 절차로 통제해야 합니다.");
    }
    private void export() {
        if(trial!=null&&trial.active) {status.setText("측정 종료 후 내보내세요.");return;}
        Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/x-ndjson");i.putExtra(Intent.EXTRA_TITLE,"zetamesh-gnss-"+System.currentTimeMillis()+".jsonl");exporting=true;startActivityForResult(i,2);
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);if(request!=2)return;exporting=false;
        if(result!=RESULT_OK||data==null||data.getData()==null)return;
        final android.net.Uri uri=data.getData(); exporting=true;
        writeTask(() -> {
            String resultText;
            try(InputStream in=new FileInputStream(events);OutputStream out=getContentResolver().openOutputStream(uri)) {
                if(out==null)throw new IOException(); byte[] bytes=new byte[8192];int n;
                while((n=in.read(bytes))!=-1)out.write(bytes,0,n);
                resultText="실제 로그 내보내기 저장됨";
            } catch(Exception e) {resultText="내보내기 실패: "+e.getClass().getSimpleName();}
            final String message=resultText;
            handler.post(() -> {exporting=false;status.setText(message);});
        });
    }
    @Override protected void onResume() {super.onResume(); if(trial!=null&&trial.active)expired(trial);}
    @Override protected void onDestroy() {
        stopTrial("destroyed"); cleanup(); handler.removeCallbacks(cleanupRetry);
        aiding.shutdownNow(); io.shutdown(); super.onDestroy();
    }
    @Override protected void onStop() {stopTrial("activity_hidden");super.onStop();}
}
