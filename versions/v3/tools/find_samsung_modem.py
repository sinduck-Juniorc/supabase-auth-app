"""List the current Samsung USB modem COM port without opening any port."""

import re


def candidates(ports):
    """Return only COM names; never expose descriptions or hardware identifiers."""
    found = set()
    for port in ports:
        name = getattr(port, "device", "")
        description = getattr(port, "description", "") or ""
        vid = getattr(port, "vid", None)
        pid = getattr(port, "pid", None)
        hwid = getattr(port, "hwid", "") or ""
        samsung_usb = (vid == 0x04E8 and pid == 0x6860) or bool(
            re.search(r"VID[_:]04E8[&:]PID[_:]6860", hwid, re.IGNORECASE)
        )
        if (re.fullmatch(r"COM[1-9][0-9]*", name, re.IGNORECASE)
                and samsung_usb and "samsung" in description.lower()
                and "modem" in description.lower()):
            found.add(name.upper())
    return sorted(found, key=lambda value: int(value[3:]))


def main():
    try:
        from serial.tools import list_ports
        ports = list_ports.comports()
    except (ImportError, OSError):
        print("포트 목록을 읽지 못했습니다. pyserial 설치와 Windows 접근 상태를 확인하세요.")
        return 2
    matches = candidates(ports)
    if not matches:
        print("일치하는 삼성 USB 모뎀 COM 포트가 없습니다. 포트를 열거나 AT 명령을 보내지 않았습니다.")
        return 1
    print("삼성 USB 모뎀 후보 COM 번호: " + ", ".join(matches))
    if len(matches) > 1:
        print("후보가 여러 개입니다. 현재 연결된 장치를 Windows 장치 관리자에서 확인하세요.")
    print("목록 정보만 확인했습니다. 포트를 열거나 AT 명령을 보내지 않았습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
