#include <ArduinoBLE.h>
#include "RelayWire.h"

SinkState sink;
uint16_t boot, beaconSeq;
uint32_t nextBeacon, stopBeacon;
bool ready, advertising, scanning;

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  boot = uint16_t(micros() ^ analogRead(A0));
  ready = BLE.begin();
  if (!ready) { Serial.println("BLE init failed"); return; }
  BLE.setConnectable(false);
  BLE.setAdvertisingInterval(64);
}

void loop() {
  if (!ready) return;
  BLE.poll();
  uint32_t now = millis();
  if (advertising && int32_t(now - stopBeacon) >= 0) {
    BLE.stopAdvertise();
    advertising = false;
  }
  if (int32_t(now - nextBeacon) >= 0) {
    if (scanning) { BLE.stopScan(); scanning = false; }
    uint8_t frame[] = {0xff, 0xff, 'Z', 'R', 1, 1, uint8_t(boot), uint8_t(boot >> 8),
                       uint8_t(beaconSeq), uint8_t(beaconSeq >> 8)};
    ++beaconSeq;
    BLEAdvertisingData ad;
    ad.setFlags(BLEFlagsGeneralDiscoverable | BLEFlagsBREDRNotSupported);
    if (ad.setManufacturerData(frame, sizeof frame)) {
      BLE.setAdvertisingData(ad);
      advertising = BLE.advertise();
    }
    nextBeacon = now + 2000;
    stopBeacon = now + 300;
  }
  if (advertising) return;
  if (!scanning) scanning = BLE.scan(true);
  BLEDevice peer = BLE.available();
  uint8_t frame[19];
  if (peer && peer.manufacturerDataLength() == sizeof frame &&
      peer.manufacturerData(frame, sizeof frame) == sizeof frame && sink.accept(frame, sizeof frame)) {
    digitalWrite(LED_BUILTIN, sink.digit ? HIGH : LOW);
    Serial.print("session="); Serial.print(sink.session, HEX);
    Serial.print(" seq="); Serial.print(sink.sequence);
    Serial.print(" received="); Serial.println(sink.digit);
  }
}
