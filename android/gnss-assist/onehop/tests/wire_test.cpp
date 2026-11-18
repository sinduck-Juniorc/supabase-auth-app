#include "../../../../firmware/uno-r4-wifi/EcoOneHop/OneHopPacket.h"
#include <stdio.h>

int main() {
  uint8_t frame[20];
  for (uint8_t digit = 0; digit <= 1; ++digit) {
    encodeDigit(frame, 0x12ab, uint16_t(65535u + digit), 160, 24000, digit);
    if (fwrite(frame, 1, sizeof frame, stdout) != sizeof frame) return 1;
  }
}
