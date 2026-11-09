package org.zetamesh.gnss;

/** 단조 시각으로만 유효성을 판정한다. 위치 좌표/모의 위치는 결과로 사용하지 않는다. */
public final class Trial {
    public final String mode;
    public final long startedNanos;
    public volatile boolean active = true;
    public boolean engineStarted = false;
    public boolean mockSeen = false;
    public boolean callbackRegistered = false;
    public Long engineTtffMs = null;
    public Long firstGpsMs = null;
    public Trial(String mode, long nanos) { this.mode = mode; this.startedNanos = nanos; }
    public boolean location(long fixNanos, long nowNanos, boolean mock) {
        if (!active) return false;
        if (mock) { mockSeen = true; return false; }
        if (fixNanos < startedNanos || fixNanos > nowNanos || nowNanos - fixNanos > 5000000000L) return false;
        if (firstGpsMs == null) firstGpsMs = (nowNanos - startedNanos) / 1000000L;
        return true;
    }
    public boolean firstFix(int millis, long nowNanos) {
        if (!active || !engineStarted || millis < 0 || millis > (nowNanos - startedNanos) / 1000000L + 500L || engineTtffMs != null) return false;
        engineTtffMs = (long) millis;
        return true;
    }
    public boolean comparable() { return engineStarted && callbackRegistered && !mockSeen && engineTtffMs != null && firstGpsMs != null; }
}
