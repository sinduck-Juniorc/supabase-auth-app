package org.zetamesh.gnss;

import android.Manifest;
import android.app.Activity;
import android.os.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.location.*;
import android.net.*;
import android.telephony.*;
import android.view.*;
import android.widget.*;
import org.json.JSONObject;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.*;

/** 사용자 조작으로만 시작하는 실외→실내 관찰. 좌표 주입과 무선 설정 변경은 하지 않는다. */
public final class WalkActivity extends Activity {
    private final Handler ui=new Handler(Looper.getMainLooper());
    private final ExecutorService files=new ThreadPoolExecutor(1,1,0L,TimeUnit.MILLISECONDS,new ArrayBlockingQueue<Runnable>(128));
    private LinearLayout root;
    private TextView guide,position,connection,phone,radio,notice;
    private Button outdoor,indoor,end,save;
    private LocationManager locations;
    private ConnectivityManager connectivity;
    private TelephonyManager telephony;
    private LocationListener gps;
    private PhoneStateListener listener;
    private Location recent;
    private boolean active=false,inside=false,exporting=false;
    private volatile boolean storageFailed=false;
    private long began, gpsBegan, lastSnapshot, serviceObservedAt, dataObservedAt;
    private int observedService=-1, observedData=-1, observedRat=0, eventSequence=0;
    private String session="",lastNetwork="",lastPhone="";
    private File log;
    private final Runnable tick=new Runnable(){public void run(){
        if(!active)return;
        long elapsed=SystemClock.elapsedRealtime()-began;
        if(elapsed>=300000){finish("time_limit");return;}
        if(gps!=null && SystemClock.elapsedRealtime()-gpsBegan>=120000){finish("location_timeout");notice.setText("위치를 얻지 못했습니다. 하늘이 보이는 곳에서 종료 후 다시 시작하세요.");return;}
        updatePosition();observeNetwork();ui.postDelayed(this,2000);
    }};
    private int dp(int x){return (int)(getResources().getDisplayMetrics().density*x+.5f);}
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        locations=(LocationManager)getSystemService(LOCATION_SERVICE);
        connectivity=(ConnectivityManager)getSystemService(CONNECTIVITY_SERVICE);
        log=new File(getFilesDir(),"walk-events.jsonl");
        ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.setBackgroundColor(Color.rgb(242,246,250));
        root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(22),dp(20),dp(22),dp(28));scroll.addView(root);setContentView(scroll);
        scroll.setOnApplyWindowInsetsListener((v,i)->{android.graphics.Insets b=i.getInsets(WindowInsets.Type.systemBars());v.setPadding(b.left,b.top,b.right,b.bottom);return i;});
        label("ZetaMesh V3 개발  ·  실내 이동 관찰",14,false);
        label("밖에서 준비하고,\n안에서 확인하세요",28,true);
        label("최근 위치와 휴대폰 통신 상태를 함께 기록합니다. 위치 주입이나 통신 가속은 실행하지 않습니다.",16,false);
        guide=card("1  실외에서 위치 준비\n2  실내의 같은 지점으로 이동\n3  결과 저장");
        position=card("최근 실외 위치\n아직 준비하지 않았습니다");
        connection=card("인터넷 경로\n관찰을 시작하면 표시됩니다");
        phone=card("휴대전화망\n위치·전화 상태 권한이 필요합니다");
        radio=card("모바일 데이터\n아직 확인하지 않았습니다");
        outdoor=button("1. 실외 위치 준비하기",()->start());
        indoor=button("2. 실내에 도착했어요",()->{
            if(!active||recent==null)return;inside=true;indoor.setEnabled(false);
            write("indoor_arrival",data("location_age_ms",age(),"accuracy_m",recent.hasAccuracy()?recent.getAccuracy():JSONObject.NULL));
            observeNetwork("indoor_arrival",true);
            guide.setText("실내 관찰 중\n같은 지점에서 잠시 기다려 주세요. 휴대전화망과 인터넷 경로는 서로 다를 수 있습니다.");
        });
        end=button("관찰 마치기",()->finish("user_finish"));
        save=button("기록 파일 저장하기",()->export());
        notice=label("화면을 유지해 주세요. 다른 앱으로 나가면 관찰을 종료합니다. 전체 5분, 위치 수신 2분 종료 예정입니다. 좌표는 파일에 저장하지 않습니다.",14,false);
        label("0.3.0-dev · "+Build.MODEL+" · Android "+Build.VERSION.RELEASE,12,false);
        controls();
    }
    private TextView label(String value,int size,boolean bold){TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(Color.rgb(24,43,61));t.setPadding(0,dp(8),0,dp(10));if(bold)t.setTypeface(null,Typeface.BOLD);root.addView(t);return t;}
    private TextView card(String value){TextView t=label(value,17,false);GradientDrawable bg=new GradientDrawable();bg.setColor(Color.WHITE);bg.setCornerRadius(dp(16));t.setBackground(bg);t.setPadding(dp(18),dp(16),dp(18),dp(16));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(12);t.setLayoutParams(lp);return t;}
    private Button button(String value,Runnable action){Button b=new Button(this);b.setText(value);b.setTextSize(16);b.setAllCaps(false);b.setMinHeight(dp(56));b.setTextColor(Color.WHITE);b.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(24,88,126)));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.bottomMargin=dp(8);root.addView(b,lp);b.setOnClickListener(v->action.run());return b;}
    private void controls(){outdoor.setEnabled(!active&&!exporting);indoor.setEnabled(active&&recent!=null&&!inside);end.setEnabled(active);save.setEnabled(!active&&!exporting);}
    private boolean granted(String p){return checkSelfPermission(p)==PackageManager.PERMISSION_GRANTED;}
    private void start(){
        if(active||exporting)return;
        if(!granted(Manifest.permission.ACCESS_FINE_LOCATION)||!granted(Manifest.permission.READ_PHONE_STATE)){
            requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION,Manifest.permission.READ_PHONE_STATE},10);
            notice.setText("정확한 위치와 전화 상태 권한을 허용한 뒤 준비 버튼을 다시 눌러 주세요. 통화·문자 내용은 읽지 않습니다.");return;
        }
        if(!locations.isLocationEnabled()){notice.setText("휴대폰 설정에서 위치 기능을 켠 뒤 돌아와 주세요.");startActivity(new Intent(android.provider.Settings.ACTION_LOCATION_SOURCE_SETTINGS));return;}
        if(!cleanup()){notice.setText("이전 구독을 해제하지 못했습니다. 앱 정보에서 강제 종료 후 다시 실행하세요.");return;}
        if(storageFailed||log.length()>=8L*1024*1024){notice.setText("기록 공간이 부족합니다. 파일을 저장한 뒤 앱 저장공간을 정리하세요.");return;}
        radio.setText("모바일 데이터\n새 상태를 기다리는 중입니다");recent=null;position.setText("최근 실외 위치\n새 위치를 기다리는 중입니다");phone.setText("휴대전화망\n상태를 확인하는 중입니다");inside=false;active=true;began=gpsBegan=SystemClock.elapsedRealtime();session=java.util.UUID.randomUUID().toString();lastNetwork=lastPhone="";lastSnapshot=0;serviceObservedAt=dataObservedAt=0;observedService=observedData=-1;observedRat=0;eventSequence=0;
        write("observation_start",data("model",Build.MODEL,"android",Build.VERSION.RELEASE,"app_version","0.3.0-dev","intervention","none"));
        guide.setText("실외 위치를 기다리는 중\n하늘이 보이는 곳에 머물러 주세요. 준비되면 실내 도착 버튼이 활성화됩니다.");
        try{
            int sub=SubscriptionManager.getDefaultDataSubscriptionId();
            telephony=(TelephonyManager)getSystemService(TELEPHONY_SERVICE);
            if(SubscriptionManager.isValidSubscriptionId(sub))telephony=telephony.createForSubscriptionId(sub);
            listener=new PhoneStateListener(){
                @Override public void onServiceStateChanged(ServiceState state){if(!active)return;observedService=state.getState();serviceObservedAt=SystemClock.elapsedRealtime();String v=service(state.getState());phone.setText("휴대전화망 · 기본 데이터 SIM\n"+v);if(!v.equals(lastPhone)){lastPhone=v;write("service_state",data("state",state.getState(),"label",v));}}
                @Override public void onDataConnectionStateChanged(int state,int type){if(active){observedData=state;observedRat=type;dataObservedAt=SystemClock.elapsedRealtime();String v=state==TelephonyManager.DATA_CONNECTED?"연결됨":state==TelephonyManager.DATA_CONNECTING?"연결 중":state==TelephonyManager.DATA_DISCONNECTED?"연결 안 됨":"일시 중단 또는 기타";
                    radio.setText("모바일 데이터: "+v+"\n망 종류: "+rat(type)+"\nOS 보고값이며 실제 통신 속도 측정은 아닙니다.");
                    write("data_connection",data("state",state,"network_type",type));}}
            };
            telephony.listen(listener,PhoneStateListener.LISTEN_SERVICE_STATE|PhoneStateListener.LISTEN_DATA_CONNECTION_STATE);
            gps=new LocationListener(){@Override public void onLocationChanged(Location l){
                if(!active||recent!=null)return;
                if(!ObservationRules.fresh(l.getElapsedRealtimeNanos(),SystemClock.elapsedRealtimeNanos(),gpsBegan*1000000L,l.isFromMockProvider()))return;
                recent=new Location(l);write("outdoor_location_ready",data("accuracy_m",l.hasAccuracy()?l.getAccuracy():JSONObject.NULL,"session_duration_ms",SystemClock.elapsedRealtime()-began));
                stopGps();if(gps!=null){finish("gps_cleanup_failed");return;}updatePosition();guide.setText("실외 위치 준비됨\n이제 안전하게 실내로 이동하세요. 도착한 지점에서 두 번째 버튼을 누르세요.");controls();
            }};
            locations.requestLocationUpdates(LocationManager.GPS_PROVIDER,1000L,0f,gps,Looper.getMainLooper());
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);ui.post(tick);controls();
        }catch(RuntimeException e){write("start_error",data("type",e.getClass().getSimpleName()));finish("start_error");}
    }
    private static String rat(int type){switch(type){case TelephonyManager.NETWORK_TYPE_NR:return "5G NR";case TelephonyManager.NETWORK_TYPE_LTE:return "LTE (5G NSA 표시와 다를 수 있음)";case TelephonyManager.NETWORK_TYPE_UMTS:case TelephonyManager.NETWORK_TYPE_HSPA:case TelephonyManager.NETWORK_TYPE_HSPAP:return "3G 계열";case TelephonyManager.NETWORK_TYPE_GPRS:case TelephonyManager.NETWORK_TYPE_EDGE:case TelephonyManager.NETWORK_TYPE_GSM:return "2G 계열";default:return "미확인 / 기타 ("+type+")";}}
    private static String service(int state){switch(state){case ServiceState.STATE_IN_SERVICE:return "서비스 이용 가능";case ServiceState.STATE_OUT_OF_SERVICE:return "서비스 범위 밖";case ServiceState.STATE_EMERGENCY_ONLY:return "긴급 통화만 가능";case ServiceState.STATE_POWER_OFF:return "무선 기능 꺼짐";default:return "확인 중";}}
    private long age(){return recent==null?-1:Math.max(0,(SystemClock.elapsedRealtimeNanos()-recent.getElapsedRealtimeNanos())/1000000L);}
    private void updatePosition(){if(recent!=null)position.setText("최근 실외 위치 · "+(age()/1000)+"초 전\n추정 정확도 "+(recent.hasAccuracy()?Math.round(recent.getAccuracy())+"m":"미확인")+"\n실내의 현재 위치가 아닙니다. 10m 이동을 확인하는 값도 아닙니다.");}
    private void observeNetwork(){observeNetwork("periodic",false);}
    private void observeNetwork(String trigger,boolean force){try{
        NetworkCapabilities d=connectivity.getNetworkCapabilities(connectivity.getActiveNetwork());
        String route=d==null?"연결 없음":d.hasTransport(NetworkCapabilities.TRANSPORT_VPN)?"VPN":d.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)?"Wi-Fi":d.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)?"셀룰러":"기타";
        boolean cell=false,validated=false;
        for(Network n:connectivity.getAllNetworks()){NetworkCapabilities c=connectivity.getNetworkCapabilities(n);if(c!=null&&c.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR)&&c.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)){cell=true;validated|=c.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED);}}
        String v="현재 인터넷 경로: "+route+"\n셀룰러 인터넷: "+(validated?"OS 검증됨":cell?"존재 · 검증 미확인":"앱에서 관측되지 않음");
        connection.setText(v);
        long now=SystemClock.elapsedRealtime();
        if(force||!v.equals(lastNetwork)||now-lastSnapshot>=15000){lastNetwork=v;lastSnapshot=now;
            write("network_snapshot",data("trigger",trigger,"phase",inside?"indoor":"outdoor","default_route",route,"cellular_internet_observed",cell,"cellular_validated",validated,
                "last_service_state",observedService,"service_callback_age_ms",serviceObservedAt==0?JSONObject.NULL:now-serviceObservedAt,
                "last_data_state",observedData,"last_network_type",observedRat,"data_callback_age_ms",dataObservedAt==0?JSONObject.NULL:now-dataObservedAt,
                "outdoor_location_age_ms",recent==null?JSONObject.NULL:age()));}
    }catch(RuntimeException e){connection.setText("통신 상태 조회 제한 · "+e.getClass().getSimpleName());
        long now=SystemClock.elapsedRealtime();if(force||now-lastSnapshot>=15000){lastSnapshot=now;write("network_query_error",data("trigger",trigger,"type",e.getClass().getSimpleName()));}}}
    private void stopGps(){if(gps==null)return;try{locations.removeUpdates(gps);gps=null;write("gps_cleanup",data("success",true));}catch(RuntimeException e){write("gps_cleanup",data("success",false));}}
    private boolean cleanup(){stopGps();if(listener!=null)try{telephony.listen(listener,PhoneStateListener.LISTEN_NONE);listener=null;write("phone_cleanup",data("success",true));}catch(RuntimeException e){write("phone_cleanup",data("success",false));}getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);return gps==null&&listener==null;}
    private void finish(String reason){if(!active){cleanup();return;}observeNetwork("finish",true);active=false;ui.removeCallbacks(tick);boolean ok=cleanup();write("observation_end",data("reason",reason,"cleanup_success",ok,"session_duration_ms",SystemClock.elapsedRealtime()-began,"indoor_marked",inside));guide.setText(ok?"관찰을 마쳤습니다\n기록 파일을 저장해 공유해 주세요. 이 기록만으로 통신 가속을 판정하지 않습니다.":"구독 해제 실패\n앱 정보에서 강제 종료해 주세요.");controls();}
    private JSONObject data(Object... values){JSONObject o=new JSONObject();try{for(int i=0;i<values.length;i+=2)o.put((String)values[i],values[i+1]);}catch(Exception e){throw new IllegalArgumentException(e);}return o;}
    private void write(String name,JSONObject o){if(storageFailed)return;try{o.put("event",name);o.put("session_id",session);o.put("schema_version",2);o.put("sequence",++eventSequence);o.put("elapsed_ms",SystemClock.elapsedRealtime());o.put("wall_utc_ms",System.currentTimeMillis());final byte[] b=(o.toString()+"\n").getBytes(StandardCharsets.UTF_8);files.execute(()->{try{if(log.length()+b.length>8L*1024*1024)throw new IOException();try(FileOutputStream f=new FileOutputStream(log,true)){f.write(b);}}catch(IOException e){failStorage();}});}catch(Exception e){failStorage();}}
    private void failStorage(){if(storageFailed)return;storageFailed=true;ui.post(()->{finish("storage_error");notice.setText("기록 공간 또는 쓰기 오류입니다. 관찰을 중단했습니다.");});}
    private void export(){if(active||exporting)return;if(!log.exists()){notice.setText("먼저 관찰을 진행해 주세요.");return;}exporting=true;controls();Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.setType("application/x-ndjson");i.addCategory(Intent.CATEGORY_OPENABLE);i.putExtra(Intent.EXTRA_TITLE,"zetamesh-walk-"+System.currentTimeMillis()+".jsonl");startActivityForResult(i,20);}
    @Override protected void onActivityResult(int request,int result,Intent intent){super.onActivityResult(request,result,intent);if(request!=20)return;if(result!=RESULT_OK||intent==null||intent.getData()==null){exporting=false;controls();return;}final Uri uri=intent.getData();try{files.execute(()->{String message;try(InputStream in=new FileInputStream(log);OutputStream out=getContentResolver().openOutputStream(uri)){if(out==null)throw new IOException();byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);message="기록 파일을 저장했습니다.";}catch(Exception e){message="저장하지 못했습니다. 다른 저장 위치를 선택해 주세요.";}final String text=message;ui.post(()->{exporting=false;controls();notice.setText(text);});});}catch(RejectedExecutionException e){exporting=false;controls();notice.setText("작업이 밀려 있습니다. 잠시 후 다시 저장해 주세요.");}}
    @Override protected void onStop(){finish("screen_hidden");super.onStop();}
    @Override protected void onDestroy(){finish("destroyed");ui.removeCallbacks(tick);files.shutdown();super.onDestroy();}
}
