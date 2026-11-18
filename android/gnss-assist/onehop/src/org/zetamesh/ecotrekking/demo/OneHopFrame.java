package org.zetamesh.ecotrekking.demo;

/** The Android scan record already separates the two-byte company ID. */
final class OneHopFrame {
    final int boot, sequence, remainingMs, digit;

    private OneHopFrame(byte[] data) {
        boot = read16(data, 5);
        sequence = read16(data, 7);
        remainingMs = read16(data, 11) - read16(data, 9);
        digit = data[15];
    }

    static int read16(byte[] data, int offset) {
        return (data[offset] & 255) | ((data[offset + 1] & 255) << 8);
    }

    private static int updateCrc(int crc, int value) {
        crc ^= (value & 255) << 8;
        for (int bit = 0; bit < 8; bit++)
            crc = ((crc & 0x8000) == 0 ? crc << 1 : (crc << 1) ^ 0x1021) & 65535;
        return crc;
    }

    static OneHopFrame parse(byte[] data) {
        if (data == null || data.length != 18 || data[0] != 'Z' || data[1] != 'M' ||
                data[2] != 1 || data[3] != 2 || data[4] != 1 || data[13] != 0 ||
                data[14] != 1 || (data[15] != 0 && data[15] != 1) ||
                read16(data, 11) != 24000 || read16(data, 9) >= 24000) return null;
        int crc = updateCrc(updateCrc(65535, 255), 255);
        for (int i = 0; i < 16; i++) crc = updateCrc(crc, data[i]);
        return crc == read16(data, 16) ? new OneHopFrame(data) : null;
    }

    static boolean newer(int previous, int next) {
        int distance = (next - previous) & 65535;
        return distance > 0 && distance < 32768;
    }
}
