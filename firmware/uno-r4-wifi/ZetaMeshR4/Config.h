#pragma once
#include <stdint.h>

// Arduino IDE에서는 이 파일의 ID와 역할만 바꾼다.
// 0: 한 대 진단, 1: Donor, 2: Relay, 3: Seeker.
#ifndef ZETAMESH_NODE_ID
#define ZETAMESH_NODE_ID 1
#endif
#ifndef ZETAMESH_ROLE
#define ZETAMESH_ROLE 0
#endif

namespace zm {
constexpr uint8_t NODE_ID = ZETAMESH_NODE_ID;
constexpr uint8_t INITIAL_ROLE = ZETAMESH_ROLE;
constexpr uint16_t PACKET_LIFETIME_MS = 24000;
constexpr uint8_t MAX_HOPS = 4;
constexpr uint32_t GENERATION_MS = 12000;
constexpr uint32_t RADIO_SLOT_MS = 3000;
constexpr uint32_t PAYLOAD_UPDATE_MS = 500;
// 광고 데이터의 유지 시간을 보수적으로 반영하는 가정값. 실측 전이다.
constexpr uint16_t AGE_GUARD_MS = 1000;
constexpr uint16_t ADV_INTERVAL_UNITS = 320;  // 0.625ms 단위, 요청값 200ms.
constexpr uint32_t STATUS_MS = 5000;
constexpr char FW_VERSION[] = "r4-0.1.0";
static_assert(NODE_ID > 0 && NODE_ID < 251, "노드 ID는 1~250이어야 합니다.");
static_assert(INITIAL_ROLE <= 3, "역할은 0~3이어야 합니다.");
static_assert(PAYLOAD_UPDATE_MS > ADV_INTERVAL_UNITS * 625UL / 1000UL + 10UL,
              "광고를 다시 시작하기 전에 요청 광고 간격과 임의 지연을 기다려야 합니다.");
}
