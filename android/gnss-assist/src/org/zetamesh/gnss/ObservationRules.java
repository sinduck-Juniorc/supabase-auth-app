package org.zetamesh.gnss;
/** 단조 시각 기반으로 이번 관찰 이후의 최근 실제 위치만 허용한다. */
public final class ObservationRules {
    public static boolean fresh(long fixNanos,long nowNanos,long startNanos,boolean mock) {
        return !mock && fixNanos>=startNanos && fixNanos<=nowNanos && nowNanos-fixNanos<=5000000000L;
    }
}
