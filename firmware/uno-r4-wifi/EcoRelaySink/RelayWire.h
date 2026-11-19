#pragma once
#include <stdint.h>

// ArduinoBLE includes the company ID at the start of manufacturer data.
inline uint32_t read32le(const uint8_t* p) {
  return uint32_t(p[0]) | uint32_t(p[1]) << 8 | uint32_t(p[2]) << 16 | uint32_t(p[3]) << 24;
}

struct SinkState {
  bool received = false;
  uint32_t session = 0, sequence = 0;
  uint8_t digit = 0;

  bool accept(const uint8_t* frame, unsigned length) {
    if (length != 19 || frame[0] != 0xff || frame[1] != 0xff ||
        frame[2] != 'Z' || frame[3] != 'R' || frame[4] != 1 ||
        frame[5] != 4 || frame[18] > 1) return false;
    uint32_t origin = read32le(frame + 10);
    uint32_t next = read32le(frame + 14);
    uint32_t distance = next - sequence;
    if (received && origin == session && (distance == 0 || distance >= 0x80000000u)) return false;
    session = origin;
    sequence = next;
    digit = frame[18];
    received = true;
    return true;
  }
};
