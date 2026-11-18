#include <ArduinoBLE.h>

BLEService probe("c142b720-fb05-4aa1-a203-a4bd332c1e41");
// ArduinoBLE stores each remote write in the local attribute value.
BLECharacteristic echo("c142b721-fb05-4aa1-a203-a4bd332c1e41", BLERead | BLEWrite, 12, true);

void setup() {
  Serial.begin(115200);
  if (!BLE.begin()) {
    Serial.println("ble_init_failed");
    return;
  }
  BLE.setAdvertisedService(probe);
  probe.addCharacteristic(echo);
  BLE.addService(probe);
  const uint8_t initial[12] = {};
  echo.writeValue(initial, sizeof initial);
  Serial.println(BLE.advertise() ? "echo_ready" : "advertise_failed");
}

void loop() {
  BLE.poll();
  delay(1);
}
