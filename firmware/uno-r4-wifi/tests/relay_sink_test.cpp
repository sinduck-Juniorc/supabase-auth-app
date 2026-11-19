#include "../EcoRelaySink/RelayWire.h"
#include <cassert>
#include <cstdio>
#include <cstring>

int main(int argc, char** argv) {
  assert(argc == 2 && std::strlen(argv[1]) == 38);
  uint8_t frame[19];
  for (unsigned i = 0; i < sizeof frame; ++i) {
    unsigned byte;
    assert(std::sscanf(argv[1] + 2*i, "%2x", &byte) == 1);
    frame[i] = uint8_t(byte);
  }
  SinkState sink;
  assert(sink.accept(frame, sizeof frame));
  assert(sink.session == 2 && sink.sequence == 3 && sink.digit == 1);
  assert(!sink.accept(frame, sizeof frame));
  frame[14] = 2;
  assert(!sink.accept(frame, sizeof frame));
  frame[14] = 4;
  frame[18] = 0;
  frame[5] = 3;
  assert(!sink.accept(frame, sizeof frame));
  frame[5] = 4;
  assert(sink.accept(frame, sizeof frame) && sink.digit == 0);
  std::puts("PC -> Android -> R4 wire test passed");
}
