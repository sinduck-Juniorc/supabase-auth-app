#include <ArduinoBLE.h>

BLEService demo("cdc62460-724d-4ace-ad2b-ac71c8371fd1");
BLEByteCharacteristic digit("cdc62461-724d-4ace-ad2b-ac71c8371fd1", BLERead | BLENotify);
bool ready = false;

void setup() {
  Serial.begin(115200);
  if (!BLE.begin()) {
    Serial.println("BLE initialization failed.");
    return;
  }
  BLE.setAdvertisedService(demo);
  demo.addCharacteristic(digit);
  BLE.addService(demo);
  digit.writeValue(255);  // No digit has been sent yet.
  ready = BLE.advertise();
  Serial.println(ready ? "Ready. Enter 0 or 1 at 115200 baud." : "Advertising failed.");
}

void loop() {
  if (!ready) return;
  BLE.poll();
  while (Serial.available()) {
    const int input = Serial.read();
    if (input != '0' && input != '1') continue;
    if (!digit.subscribed()) {
      Serial.println("Connect the phone app first.");
      continue;
    }
    const byte value = byte(input - '0');
    if (digit.writeValue(value)) {
      Serial.print("Notified: ");
      Serial.println(value);
    } else {
      Serial.println("Notification failed.");
    }
  }
}
