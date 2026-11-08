#include <ArduinoBLE.h>
#include "Config.h"
#include "Protocol.h"

// 진단/고정 기준선용이다. 실제 GNSS 주입·제타/체비쇼프 정책은 이 단계에서 사용하지 않는다.
constexpr uint8_t RADIO_STOP = 0, RADIO_TX = 1, RADIO_RX = 2;
const char* ROLE_NAMES[] = { "diagnostic", "donor", "relay", "seeker" };
uint8_t role = zm::INITIAL_ROLE, radioMode = RADIO_STOP, forcedMode = RADIO_STOP;
bool radioReady = false, havePacket = false;
uint16_t bootNonce = 0, sequenceNumber = 0;
uint32_t stateSince = 0, packetReferencedAt = 0, lastGenerated = 0;
uint32_t lastPayload = 0, lastStatus = 0, lastInit = 0;
uint32_t txUpdates = 0, rxNew = 0, duplicates = 0, invalidFrames = 0, hopDrops = 0, expired = 0, scanObservations = 0;
uint8_t airFrame[zm::FRAME_SIZE];
char localName[20];
zm::Packet held = {};
zm::SeenCache seen;

void logPrefix(const char* event) {
  Serial.print(F("{\"event\":\"")); Serial.print(event);
  Serial.print(F("\",\"uptime_ms\":")); Serial.print(millis());
  Serial.print(F(",\"node_id\":")); Serial.print(zm::NODE_ID);
  Serial.print(F(",\"role\":\"")); Serial.print(ROLE_NAMES[role]); Serial.print('"');
  Serial.print(F(",\"firmware\":\"")); Serial.print(zm::FW_VERSION); Serial.print('"');
}

void logState(const char* event) { logPrefix(event); Serial.println('}'); }

void logPacket(const char* event, const zm::Packet& packet, int rssi, bool received) {
  logPrefix(event);
  Serial.print(F(",\"kind\":\"virtual_gnss\",\"source_id\":")); Serial.print(packet.source);
  Serial.print(F(",\"sender_id\":")); Serial.print(packet.sender);
  Serial.print(F(",\"boot_nonce\":")); Serial.print(packet.boot);
  Serial.print(F(",\"sequence\":")); Serial.print(packet.sequence);
  Serial.print(F(",\"source_created_ms\":")); Serial.print(packet.created_ms);
  Serial.print(F(",\"age_ms\":")); Serial.print(packet.age_ms);
  Serial.print(F(",\"lifetime_ms\":")); Serial.print(packet.lifetime_ms);
  Serial.print(F(",\"hops\":")); Serial.print(packet.hops + (received ? 1 : 0));
  Serial.print(F(",\"max_hops\":")); Serial.print(packet.max_hops);
  Serial.print(F(",\"rssi_dbm\":"));
  if (received && rssi < 0) Serial.print(rssi); else Serial.print(F("null"));
  Serial.println(F(",\"gnss_quality\":null,\"battery_soc\":null}"));
}

void logStatus() {
  logPrefix("status");
  Serial.print(F(",\"mode\":\"")); Serial.print(radioMode == RADIO_TX ? "advertise" : radioMode == RADIO_RX ? "scan" : "stopped");
  Serial.print(F("\",\"tx_updates\":")); Serial.print(txUpdates);
  Serial.print(F(",\"rx_new\":")); Serial.print(rxNew);
  Serial.print(F(",\"duplicates\":")); Serial.print(duplicates);
  Serial.print(F(",\"invalid\":")); Serial.print(invalidFrames);
  Serial.print(F(",\"hop_drops\":")); Serial.print(hopDrops);
  Serial.print(F(",\"expired_local\":")); Serial.print(expired);
  Serial.print(F(",\"scan_observations\":")); Serial.print(scanObservations);
  Serial.println('}');
}

void generateOwn(uint32_t now) {
  held = { zm::NODE_ID, zm::NODE_ID, bootNonce, ++sequenceNumber, now, 0,
           zm::PACKET_LIFETIME_MS, 0, zm::MAX_HOPS, zm::MISSING, zm::MISSING };
  packetReferencedAt = lastGenerated = now;
  havePacket = true;
  logPacket("generated_virtual", held, 0, false);
}

bool currentPacket(uint32_t now, zm::Packet& packet) {
  if (!havePacket) return false;
  packet = held;
  if (!zm::advance(packet, uint32_t(now - packetReferencedAt))) {
    havePacket = false; ++expired; logState("expired"); return false;
  }
  return true;
}

bool updateAdvertising(uint32_t now) {
  BLE.stopAdvertise();
  now = millis();
  zm::Packet packet;
  if (!currentPacket(now, packet) || packet.hops >= packet.max_hops || !zm::advance(packet, zm::AGE_GUARD_MS)) return false;
  if (!zm::encode(packet, airFrame, sizeof airFrame)) return false;
  BLEAdvertisingData advertising;
  BLEAdvertisingData response;
  if (!advertising.setFlags(BLEFlagsGeneralDiscoverable | BLEFlagsBREDRNotSupported) ||
      !advertising.setManufacturerData(airFrame, sizeof airFrame) || !response.setLocalName(localName)) {
    logState("advertisement_too_large"); return false;
  }
  BLE.setAdvertisingData(advertising);
  BLE.setScanResponseData(response);
  if (!BLE.advertise()) { logState("advertise_failed"); return false; }
  lastPayload = millis();
  ++txUpdates;  // API 갱신 횟수다. 실제 RF 송신 프레임 수가 아니다.
  if (txUpdates == 1 || txUpdates % 10 == 0) logPacket("advertise_update", packet, 0, false);
  return true;
}

void startMode(uint8_t requested, uint32_t now) {
  if (!radioReady) return;
  BLE.stopAdvertise(); BLE.stopScan();
  radioMode = RADIO_STOP;
  if (requested == RADIO_TX && updateAdvertising(now)) radioMode = RADIO_TX;
  else {
    if (requested == RADIO_TX) logState("exploration_fallback");
    if (BLE.scan(true)) radioMode = RADIO_RX;
    else logState("scan_failed");
  }
  stateSince = millis();
  logState(radioMode == RADIO_TX ? "mode_advertise" : radioMode == RADIO_RX ? "mode_scan" : "radio_stopped");
}

void receivePacket(uint32_t now) {
  BLEDevice peer = BLE.available();
  if (!peer) return;
  now = millis();
  ++scanObservations;
  if (peer.manufacturerDataLength() != int(zm::FRAME_SIZE)) return;
  uint8_t raw[zm::FRAME_SIZE];
  if (peer.manufacturerData(raw, sizeof raw) != int(sizeof raw)) return;
  if (raw[0] != 0xff || raw[1] != 0xff || raw[2] != 'Z' || raw[3] != 'M') return;
  zm::Packet packet;
  if (!zm::decode(raw, sizeof raw, packet)) { ++invalidFrames; logState("invalid_frame"); return; }
  if (packet.max_hops != zm::MAX_HOPS) { ++invalidFrames; logState("invalid_frame"); return; }
  if (packet.sender == zm::NODE_ID) return;
  if (packet.hops >= packet.max_hops) { ++hopDrops; logState("hop_limit"); return; }
  if (seen.contains(packet, now)) { ++duplicates; return; }
  seen.insert(packet, now);
  ++rxNew;
  logPacket("received_virtual", packet, peer.rssi(), true);
  if (role != 2) return;
  if (!zm::forward(packet, zm::NODE_ID, 0) || packet.hops >= packet.max_hops) return;
  zm::Packet old;
  if (!currentPacket(now, old) || packet.age_ms < old.age_ms ||
      (packet.age_ms == old.age_ms && packet.hops < old.hops)) {
    held = packet; packetReferencedAt = now; havePacket = true;
    logPacket("relay_queued", packet, 0, false);
  }
}

void initializeRadio(uint32_t now) {
  lastInit = now;
  if (!BLE.begin()) { BLE.end(); logState("ble_init_failed"); return; }
  radioReady = true;
  BLE.setConnectable(false);
  BLE.setAdvertisingInterval(zm::ADV_INTERVAL_UNITS);
  logState("ble_ready");
  startMode(role == 2 || role == 3 ? RADIO_RX : RADIO_TX, millis());
}

void changeRole(uint8_t next, uint8_t forced, uint32_t now) {
  role = next; forcedMode = forced; havePacket = false; seen.clear();
  if (role == 0 || role == 1) generateOwn(now);
  logState("role_changed");
  startMode(forcedMode ? forcedMode : role == 2 || role == 3 ? RADIO_RX : RADIO_TX, now);
}

void processSerial(uint32_t now) {
  while (Serial.available()) {
    const char command = char(Serial.read());
    switch (command) {
      case 'a': changeRole(0, RADIO_TX, now); break;
      case 's': changeRole(0, RADIO_RX, now); break;
      case 'c': changeRole(0, RADIO_STOP, now); break;
      case 'd': changeRole(1, RADIO_STOP, now); break;
      case 'r': changeRole(2, RADIO_STOP, now); break;
      case 'k': changeRole(3, RADIO_STOP, now); break;
      case 'i': logStatus(); break;
      case 'h':
        logPrefix("help"); Serial.println(F(",\"commands\":\"a=advertise s=scan c=cycle d=donor r=relay k=seeker i=status h=help\"}")); break;
      default: break;
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(300);  // 콘솔 접속을 무한히 기다리지 않는다.
  snprintf(localName, sizeof localName, "ZetaMesh-R4-%02u", zm::NODE_ID);
  // 시험용 식별자이며 암호학적 난수/재부팅 간 유일성을 보장하지 않는다.
  bootNonce = uint16_t(uint32_t(analogRead(A0)) ^ micros());
  logPrefix("boot"); Serial.print(F(",\"board\":\"UNO_R4_WiFi\",\"build\":\"")); Serial.print(__DATE__ " " __TIME__);
  Serial.println(F("\",\"manufacturer_bytes\":26,\"advertising_bytes\":31,\"gnss\":\"virtual_only\",\"power_measured\":false}"));
  if (role == 0 || role == 1) generateOwn(millis());
  initializeRadio(millis());
}

void loop() {
  uint32_t now = millis();
  processSerial(now);
  if (!radioReady) {
    if (uint32_t(now - lastInit) >= 5000) initializeRadio(now);
    delay(1); return;
  }
  BLE.poll();
  now = millis();
  if ((role == 0 || role == 1) && uint32_t(now - lastGenerated) >= zm::GENERATION_MS) generateOwn(now);
  if (radioMode == RADIO_RX) receivePacket(now);
  if (radioMode == RADIO_TX && uint32_t(now - lastPayload) >= zm::PAYLOAD_UPDATE_MS) {
    if (!updateAdvertising(now)) startMode(RADIO_RX, now);
  }
  // HCI 호출과 모드 전환 뒤의 시각을 사용해 새 stateSince와의 뺄셈을 처리한다.
  now = millis();
  if (!forcedMode && (role == 0 || role == 2) && uint32_t(now - stateSince) >= zm::RADIO_SLOT_MS) {
    startMode(radioMode == RADIO_TX ? RADIO_RX : RADIO_TX, now);
  }
  if (radioMode == RADIO_STOP && uint32_t(now - stateSince) >= 5000) startMode(RADIO_RX, now);
  if (uint32_t(now - lastStatus) >= zm::STATUS_MS) { logStatus(); lastStatus = now; }
  delay(1);
}
