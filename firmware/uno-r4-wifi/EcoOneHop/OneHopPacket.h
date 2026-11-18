#pragma once
#include <stdint.h>
#include <string.h>

inline void put16(uint8_t* dest, uint16_t n) { dest[0] = n; dest[1] = n >> 8; }

inline void encodeDigit(uint8_t (&frame)[20], uint16_t boot, uint16_t sequence,
                        uint16_t age, uint16_t lifetime, uint8_t digit) {
  const uint8_t prefix[] = {0xff, 0xff, 'Z', 'M', 1, 2, 1};
  memcpy(frame, prefix, sizeof prefix);
  put16(frame + 7, boot);
  put16(frame + 9, sequence);
  put16(frame + 11, age);
  put16(frame + 13, lifetime);
  frame[15] = 0;
  frame[16] = 1;
  frame[17] = digit;
  uint16_t crc = 0xffff;
  for (int i = 0; i < 18; ++i) {
    crc ^= uint16_t(frame[i]) << 8;
    for (int bit = 0; bit < 8; ++bit)
      crc = crc & 0x8000 ? (crc << 1) ^ 0x1021 : crc << 1;
  }
  put16(frame + 18, crc);
}
