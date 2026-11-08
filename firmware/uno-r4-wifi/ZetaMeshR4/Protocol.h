#pragma once
#include <stdint.h>
#include <stddef.h>

namespace zm {
// Flags 3바이트 + Manufacturer AD 헤더 2바이트 + 본문 26바이트 = 31바이트.
constexpr size_t FRAME_SIZE = 26;
constexpr uint8_t VERSION = 1;
constexpr uint8_t VIRTUAL_GNSS = 1;
constexpr uint8_t MISSING = 255;

struct Packet {
  uint8_t source;
  uint8_t sender;
  uint16_t boot;
  uint16_t sequence;
  uint32_t created_ms;  // 원본 노드의 부팅 후 시각. UTC가 아니다.
  uint16_t age_ms;      // 누적 연령; 수신 노드의 시계와 직접 비교하지 않는다.
  uint16_t lifetime_ms;
  uint8_t hops;
  uint8_t max_hops;
  uint8_t quality;      // 0~100 또는 255(미측정).
  uint8_t battery;      // 0~100 또는 255(미측정).
};

inline uint16_t read16(const uint8_t* p) { return uint16_t(p[0]) | uint16_t(uint16_t(p[1]) << 8); }
inline uint32_t read32(const uint8_t* p) { return uint32_t(read16(p)) | (uint32_t(read16(p + 2)) << 16); }
inline void put16(uint8_t* p, uint16_t x) { p[0] = uint8_t(x); p[1] = uint8_t(x >> 8); }
inline void put32(uint8_t* p, uint32_t x) { put16(p, uint16_t(x)); put16(p + 2, uint16_t(x >> 16)); }

inline uint16_t crc16(const uint8_t* data, size_t size) {
  uint16_t crc = 0xffff;
  for (size_t i = 0; i < size; ++i) {
    crc ^= uint16_t(data[i]) << 8;
    for (uint8_t b = 0; b < 8; ++b) crc = uint16_t((crc & 0x8000) ? (crc << 1) ^ 0x1021 : crc << 1);
  }
  return crc;
}

inline bool valid(const Packet& p) {
  return p.source > 0 && p.source <= 250 && p.sender > 0 && p.sender <= 250 &&
    p.lifetime_ms >= 1000 && p.lifetime_ms <= 60000 && p.age_ms < p.lifetime_ms &&
    p.max_hops > 0 && p.max_hops <= 8 && p.hops <= p.max_hops &&
    (p.quality <= 100 || p.quality == MISSING) && (p.battery <= 100 || p.battery == MISSING);
}

inline bool encode(const Packet& p, uint8_t* out, size_t size) {
  if (!out || size != FRAME_SIZE || !valid(p)) return false;
  out[0] = out[1] = 0xff;  // 실험용 company ID. 상용 제품 식별자로 사용하지 않는다.
  out[2] = 'Z'; out[3] = 'M'; out[4] = VERSION; out[5] = VIRTUAL_GNSS;
  out[6] = p.source; out[7] = p.sender; put16(out + 8, p.boot); put16(out + 10, p.sequence);
  put32(out + 12, p.created_ms); put16(out + 16, p.age_ms); put16(out + 18, p.lifetime_ms);
  out[20] = p.hops; out[21] = p.max_hops; out[22] = p.quality; out[23] = p.battery;
  put16(out + 24, crc16(out, 24));
  return true;
}

inline bool decode(const uint8_t* data, size_t size, Packet& p) {
  if (!data || size != FRAME_SIZE || data[0] != 0xff || data[1] != 0xff ||
      data[2] != 'Z' || data[3] != 'M' || data[4] != VERSION || data[5] != VIRTUAL_GNSS ||
      read16(data + 24) != crc16(data, 24)) return false;
  Packet parsed = { data[6], data[7], read16(data + 8), read16(data + 10), read32(data + 12),
    read16(data + 16), read16(data + 18), data[20], data[21], data[22], data[23] };
  if (!valid(parsed)) return false;
  p = parsed;
  return true;
}

inline bool advance(Packet& p, uint32_t elapsed_ms) {
  // 더하기 전에 남은 수명과 비교해 16/32비트 넘침을 막는다.
  if (!valid(p) || elapsed_ms >= uint32_t(p.lifetime_ms - p.age_ms)) return false;
  p.age_ms = uint16_t(p.age_ms + elapsed_ms);
  return true;
}

inline bool forward(Packet& p, uint8_t sender, uint32_t elapsed_ms) {
  Packet copy = p;
  if (sender == 0 || sender > 250 || !advance(copy, elapsed_ms) || copy.hops >= copy.max_hops) return false;
  copy.sender = sender;
  ++copy.hops;
  p = copy;
  return true;
}

inline bool sameId(const Packet& a, const Packet& b) {
  return a.source == b.source && a.boot == b.boot && a.sequence == b.sequence && a.created_ms == b.created_ms;
}

class SeenCache {
  struct Entry { Packet packet; uint32_t received_ms; bool used; } entries_[16] = {};
  uint8_t cursor_ = 0;
public:
  bool contains(const Packet& p, uint32_t now) {
    for (auto& entry : entries_) {
      if (!entry.used) continue;
      Packet aged = entry.packet;
      if (!advance(aged, uint32_t(now - entry.received_ms))) { entry.used = false; continue; }
      if (sameId(entry.packet, p)) return true;
    }
    return false;
  }
  void insert(const Packet& p, uint32_t now) {
    entries_[cursor_] = { p, now, true };
    cursor_ = uint8_t((cursor_ + 1) % 16);
  }
  void clear() { for (auto& entry : entries_) entry.used = false; cursor_ = 0; }
};
}
