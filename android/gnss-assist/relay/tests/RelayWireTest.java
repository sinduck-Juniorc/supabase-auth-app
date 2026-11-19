package org.zetamesh.gnss.v3.relay;

public final class RelayWireTest {
    public static void main(String[] args) {
        String[] hex = args[0].split("-");
        byte[] input = new byte[hex.length];
        for (int i = 0; i < hex.length; ++i) input[i] = (byte)Integer.parseInt(hex[i], 16);
        if (RelayWire.forward(input, 2) != null || RelayWire.forward(new byte[0], 1) != null)
            throw new AssertionError("target or length");
        byte[] output = RelayWire.forward(input, 1);
        if (output == null || RelayWire.i32(output, 8) != 2 || RelayWire.i32(output, 12) != 3 ||
                output[16] != 1 || RelayWire.forward(output, 1) != null) throw new AssertionError("route");
        input[16] = 2;
        if (RelayWire.forward(input, 1) != null) throw new AssertionError("invalid digit");
        System.out.print("ffff"); // ArduinoBLE includes company ID in the scan record.
        for (byte b : output) System.out.printf("%02x", b & 255);
        System.out.println();
    }
}
