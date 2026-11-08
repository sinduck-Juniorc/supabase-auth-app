#include "../ZetaMeshR4/Protocol.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

int main() {
  using namespace zm;
  static_assert(FRAME_SIZE + 2 + 3 == 31, "legacy 광고 크기");
  const uint8_t known[] = {'1','2','3','4','5','6','7','8','9'};
  assert(crc16(known, sizeof known) == 0x29b1);  // CRC-16/CCITT-FALSE 표준 벡터.
  Packet original = {1, 1, 0xabcd, 0x1234, 0x12345678, 0, 24000, 0, 4, MISSING, MISSING};
  uint8_t bytes[FRAME_SIZE];
  assert(encode(original, bytes, sizeof bytes));
  assert(bytes[8] == 0xcd && bytes[9] == 0xab && bytes[10] == 0x34 && bytes[11] == 0x12);
  assert(bytes[12] == 0x78 && bytes[13] == 0x56 && bytes[14] == 0x34 && bytes[15] == 0x12);
  Packet parsed = {};
  assert(decode(bytes, sizeof bytes, parsed) && sameId(original, parsed));
  assert(parsed.quality == MISSING && parsed.battery == MISSING);
  assert(!decode(nullptr, FRAME_SIZE, parsed) && !decode(bytes, FRAME_SIZE - 1, parsed));
  assert(!encode(original, nullptr, FRAME_SIZE));
  for (size_t i = 0; i < FRAME_SIZE; ++i) {
    uint8_t corrupt[FRAME_SIZE]; memcpy(corrupt, bytes, sizeof bytes); corrupt[i] ^= 1;
    assert(!decode(corrupt, sizeof corrupt, parsed));
  }
  uint8_t unknownVersion[FRAME_SIZE]; memcpy(unknownVersion, bytes, sizeof bytes);
  unknownVersion[4] = 2; put16(unknownVersion + 24, crc16(unknownVersion, 24));
  assert(!decode(unknownVersion, sizeof unknownVersion, parsed));
  Packet packet = original;
  assert(advance(packet, 23999));
  assert(!advance(packet, 1));
  assert(packet.age_ms == 23999);  // 실패하면 입력을 변경하지 않는다.
  assert(!advance(packet, 0xffffffffUL));
  packet = original;
  assert(forward(packet, 2, 50) && packet.hops == 1 && packet.sender == 2 && packet.age_ms == 50);
  assert(forward(packet, 3, 50) && packet.hops == 2);
  assert(forward(packet, 4, 50) && forward(packet, 5, 50));
  assert(!forward(packet, 6, 0));
  assert(!forward(packet, 0, 0));
  assert(sameId(packet, original));
  packet = original; packet.age_ms = packet.lifetime_ms;
  assert(!valid(packet) && !encode(packet, bytes, sizeof bytes));
  packet = original; packet.quality = 101; assert(!valid(packet));
  packet = original; packet.battery = 254; assert(!valid(packet));
  packet = original; packet.max_hops = 0; assert(!valid(packet));
  SeenCache seen;
  assert(!seen.contains(original, 100)); seen.insert(original, 100);
  assert(seen.contains(original, 23999 + 100));
  assert(!seen.contains(original, 24000 + 100));
  // millis()의 32비트 순환 경계에서도 상대 만료 시간이 맞아야 한다.
  seen.insert(original, 0xfffffff0UL);
  assert(seen.contains(original, 0x10));
  assert(!seen.contains(original, uint32_t(0xfffffff0UL + 24000UL)));
  seen.insert(original, 100); seen.clear(); assert(!seen.contains(original, 101));
  // 가상 A→B→C의 순수 프로토콜 검사다. RF 실물 전달 증거가 아니다.
  Packet relay = original; assert(forward(relay, 2, 3000));
  assert(encode(relay, bytes, sizeof bytes) && decode(bytes, sizeof bytes, parsed));
  assert(parsed.source == 1 && parsed.sender == 2 && parsed.hops + 1 == 2);
  puts("프로토콜 검사 통과: CRC, 직렬화, 오류 입력, 수명, 홉, 중복, 시계 순환, 논리적 2홉");
}
