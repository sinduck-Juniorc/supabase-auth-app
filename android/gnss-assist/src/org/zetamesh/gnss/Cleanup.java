package org.zetamesh.gnss;
/** 한 자원의 해제 실패가 다른 자원 해제를 막지 않도록 한다. */
public final class Cleanup {
    public static boolean run(Runnable... actions) {
        boolean success=true;
        for(Runnable action:actions) {
            try {action.run();} catch(RuntimeException e) {success=false;}
        }
        return success;
    }
}
