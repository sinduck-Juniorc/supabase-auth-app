"""Send four paced test inputs to an Arduino UNO R4 WiFi."""

import argparse
import re
import sys
import time


DIGITS = (b"0", b"1", b"0", b"1")
INTERVAL_SECONDS = 3
# USB identifiers registered for UNO R4 WiFi in ArduinoCore-renesas boards.txt.
R4_WIFI_USB_IDS = {(0x2341, 0x1002), (0x2341, 0x006D)}


def r4_ports(ports):
    return sorted({
        port.device.upper()
        for port in ports
        if (port.vid, port.pid) in R4_WIFI_USB_IDS
        and re.fullmatch(r"COM[1-9][0-9]*", port.device, re.IGNORECASE)
    }, key=lambda name: int(name[3:]))


def send_digits(connection):
    started = next_write = time.monotonic()
    for index, digit in enumerate(DIGITS, 1):
        remaining = next_write - time.monotonic()
        if remaining > 0:
            time.sleep(remaining)
        sent_at = time.monotonic()
        if connection.write(digit) != len(digit):
            raise OSError("incomplete serial write")
        print(f"{index}/{len(DIGITS)}  +{sent_at - started:.3f}s  {digit.decode('ascii')}", flush=True)
        next_write = sent_at + INTERVAL_SECONDS


def main(argv=None):
    parser = argparse.ArgumentParser(description="UNO R4 WiFi에 0, 1, 0, 1을 3초 간격으로 한 번 전송합니다.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="UNO R4 WiFi COM 포트만 표시합니다.")
    mode.add_argument("--port", type=str.upper, help="전송할 UNO R4 WiFi COM 포트")
    args = parser.parse_args(argv)
    try:
        import serial
        from serial.tools import list_ports
    except ImportError:
        parser.error("pyserial 필요: python -m pip install pyserial==3.5")

    try:
        ports = r4_ports(list_ports.comports())
        if args.list:
            print("\n".join(ports) or "UNO R4 WiFi COM 포트를 찾지 못했습니다.")
            return 0 if ports else 1
        if args.port not in ports:
            parser.error("지정한 포트가 UNO R4 WiFi로 확인되지 않았습니다. --list로 확인하세요.")
        with serial.Serial(args.port, baudrate=115200, write_timeout=1) as connection:
            time.sleep(2)  # Allow the board to settle after the serial port opens.
            send_digits(connection)
    except OSError:
        print("직렬 연결 또는 쓰기 오류로 중단했습니다. IDE 시리얼 모니터와 USB 연결을 확인하세요.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n전송을 중단했습니다.", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
