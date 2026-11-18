#include <ArduinoBLE.h>
#include "OneHopPacket.h"

// Manufacturer data: lab company ID, ZM, version, binary kind, donor ID,
// boot ID, sequence, age, lifetime (little endian), hops, limit, digit, CRC.
const uint8_t peerBeacon[] = {0xff, 0xff, 'Z', 'M', 1, 3, 2};
const uint32_t lifetime = 24000;
const uint16_t txWindow = 160;
bool ready, scanning, transmitting, seenPeer, hasDigit, pending, previousSaving;
uint16_t bootId, sequence;
uint8_t digit;
uint32_t created, lastPeer, txStart, nextTx, scanStart;

void stopScan() {
  if (scanning) BLE.stopScan();
  scanning = false;
}

void sendBurst(uint32_t now, bool saving) {
  stopScan();
  uint8_t frame[20];
  encodeDigit(frame, bootId, sequence, uint16_t(now - created) + txWindow, lifetime, digit);
  BLEAdvertisingData advertising;
  advertising.setFlags(BLEFlagsGeneralDiscoverable | BLEFlagsBREDRNotSupported);
  if (advertising.setManufacturerData(frame, sizeof frame)) {
    BLE.setAdvertisingData(advertising);
    transmitting = BLE.advertise();
  }
  txStart = millis();
  nextTx = now + (saving ? 1600 : 800);
  if (transmitting) pending = false;
  else Serial.println("advertise_failed");
}

void setup() {
  Serial.begin(115200);
  bootId = uint16_t(micros() ^ analogRead(A0));
  ready = BLE.begin();
  if (!ready) { Serial.println("ble_init_failed"); return; }
  BLE.setConnectable(false);
  BLE.setAdvertisingInterval(64);  // 40 ms inside each advertising burst.
  scanStart = millis();
}

void loop() {
  if (!ready) return;
  BLE.poll();
  uint32_t now = millis();
  while (Serial.available()) {
    int input = Serial.read();
    if (input != '0' && input != '1') continue;
    if (transmitting) { BLE.stopAdvertise(); transmitting = false; }
    digit = input - '0';
    ++sequence;
    created = nextTx = now;
    hasDigit = pending = true;
    Serial.print("queued "); Serial.println(digit);
  }
  if (transmitting && now - txStart >= txWindow) {
    BLE.stopAdvertise();
    transmitting = false;
  }
  if (transmitting) return;
  if (scanning) {
    BLEDevice device = BLE.available();
    uint8_t data[sizeof peerBeacon];
    if (device && device.manufacturerDataLength() == sizeof data &&
        device.manufacturerData(data, sizeof data) == sizeof data &&
        memcmp(data, peerBeacon, sizeof data) == 0) {
      lastPeer = now;
      seenPeer = true;
    }
  }
  if (seenPeer && now - lastPeer >= 5000) seenPeer = false;
  if (hasDigit && now - created >= lifetime - txWindow) hasDigit = pending = false;
  bool saving = seenPeer && hasDigit && now - created < 15000 && !pending;
  if (saving != previousSaving) {
    Serial.println(saving ? "scan=60/600 burst=1600ms" : "scan=180/600 burst=800ms");
    previousSaving = saving;
  }
  if (hasDigit && int32_t(now - nextTx) >= 0) { sendBurst(now, saving); return; }
  if (now - scanStart >= 600) scanStart = now;
  bool listen = now - scanStart < (saving ? 60u : 180u);
  if (listen && !scanning) scanning = BLE.scan(true);
  if (!listen) stopScan();
  delay(1);
}
