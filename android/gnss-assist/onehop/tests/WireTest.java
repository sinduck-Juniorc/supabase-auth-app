package org.zetamesh.ecotrekking.demo;

import java.util.Arrays;

public final class WireTest {
    public static void main(String[] args) throws Exception {
        for (int digit = 0; digit <= 1; digit++) {
            byte[] raw = System.in.readNBytes(20);
            if (raw.length != 20 || raw[0] != -1 || raw[1] != -1) throw new AssertionError();
            byte[] body = Arrays.copyOfRange(raw, 2, raw.length);
            OneHopFrame frame = OneHopFrame.parse(body);
            int expectedSequence = digit == 0 ? 65535 : 0;
            if (frame == null || frame.digit != digit || frame.boot != 0x12ab ||
                    frame.remainingMs != 23840 || frame.sequence != expectedSequence) throw new AssertionError();
            body[15] ^= 1;
            if (OneHopFrame.parse(body) != null) throw new AssertionError("corrupt payload accepted");
        }
        if (!OneHopFrame.newer(65535, 0) || OneHopFrame.newer(0, 65535) ||
                OneHopFrame.newer(0, 0)) throw new AssertionError("sequence ordering");
        System.out.println("R4 encoder -> Android decoder: 0, 1, CRC and rollover passed");
    }
}
