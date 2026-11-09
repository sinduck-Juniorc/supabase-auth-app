import org.zetamesh.gnss.Trial;
import org.zetamesh.gnss.Cleanup;
public class TrialTest {
    static void check(boolean b) { if(!b)throw new AssertionError(); }
    public static void main(String[] args) {
        for(int failed=0;failed<3;failed++) {
            final int failure=failed; final int[] called={0};
            Runnable[] actions=new Runnable[3];
            for(int i=0;i<3;i++) { final int index=i; actions[i]=() -> {
                called[0]++; if(index==failure)throw new IllegalStateException("시험 예외");
            }; }
            check(!Cleanup.run(actions)); check(called[0]==3);
        }
        check(Cleanup.run(() -> {}, () -> {}, () -> {}));
        System.out.println("통과: 각 위치에서 해제 예외가 나도 모든 자원 정리 시도");
        Trial t=new Trial("baseline",10000000000L);
        check(!t.firstFix(50,11000000000L));
        check(!t.location(9000000000L,11000000000L,false));
        check(!t.location(12000000000L,11000000000L,false));
        check(!t.location(10000000000L,17000000000L,false));
        check(t.location(11000000000L,12000000000L,false));check(t.firstGpsMs==2000L);
        t.engineStarted=true;t.callbackRegistered=true;check(!t.firstFix(20000,12000000000L));check(t.firstFix(1500,12000000000L));check(!t.firstFix(1600,12000000000L));check(t.comparable());
        t.active=false;check(!t.location(13000000000L,14000000000L,false));
        Trial mock=new Trial("assisted",0);mock.engineStarted=true;mock.callbackRegistered=true;mock.firstFix(500,1000000000L);check(!mock.location(1000000000L,1000000000L,true));check(!mock.comparable());
        System.out.println("통과: 캐시·미래·오래된·모의 위치 제외, 시작 콜백·중복·종료 검증");
    }
}
