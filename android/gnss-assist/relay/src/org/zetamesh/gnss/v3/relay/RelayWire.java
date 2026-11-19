package org.zetamesh.gnss.v3.relay;

final class RelayWire {
    static final int COMPANY = 0xffff;
    static boolean is(byte[] b, int kind, int length) {
        return b != null && b.length == length && b[0] == 'Z' && b[1] == 'R' && b[2] == 1 && b[3] == kind;
    }
    static int u16(byte[] b, int off) {
        return (b[off] & 255) | ((b[off+1] & 255) << 8);
    }
    static int i32(byte[] b, int off) {
        return u16(b, off) | (u16(b, off + 2) << 16);
    }
    static byte[] offer(int relay, int battery, int rssi, int reception, int age) {
        return new byte[]{'Z','R',1,2,(byte)relay,(byte)(relay >> 8),(byte)(relay >> 16),(byte)(relay >> 24),
                (byte)battery,(byte)rssi,(byte)reception,(byte)age};
    }
    static byte[] forward(byte[] input, int relay) {
        if (!is(input, 3, 17) || i32(input, 4) != relay || (input[16] & 255) > 1) return null;
        byte[] out = input.clone();
        out[3] = 4;
        return out;
    }
}
