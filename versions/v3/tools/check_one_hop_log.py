"""Check the latest one-hop field-test session without printing log records."""

import argparse
import json
from pathlib import Path
import sys


def latest_session(lines):
    sessions = {}
    latest_id = None
    for number, line in enumerate(lines, 1):
        try:
            entry = json.loads(line)
        except (ValueError, RecursionError):
            raise ValueError(f"{number}행: JSON 형식 오류") from None
        if not isinstance(entry, dict):
            raise ValueError(f"{number}행: JSON 객체가 필요합니다.")
        session_id = entry.get("session_id")
        event = entry.get("event")
        if not isinstance(session_id, str) or not session_id or not isinstance(event, str):
            raise ValueError(f"{number}행: 세션 또는 이벤트 필드 오류")
        sessions.setdefault(session_id, []).append(entry)
        if event == "session_start":
            latest_id = session_id
    if latest_id is None:
        raise ValueError("세션 시작 기록이 없습니다.")
    return sessions[latest_id]


def check_session(entries):
    events = [entry["event"] for entry in entries]
    if events[0] != "session_start" or events.count("session_start") != 1:
        raise ValueError("최신 세션의 시작 기록이 올바르지 않습니다.")
    if events[-1] != "session_end" or events.count("session_end") != 1:
        raise ValueError("최신 세션의 종료 기록이 올바르지 않습니다.")

    packets = [entry for entry in entries if entry["event"] == "packet_received"]
    digits = [entry.get("digit") for entry in packets]
    boots = [entry.get("sender_boot_id") for entry in packets]
    sequences = [entry.get("sequence") for entry in packets]
    end = entries[-1]
    count = end.get("received_count")
    return {
        "received": len(packets),
        "expected_digits": all(type(digit) is int for digit in digits) and digits == [0, 1, 0, 1],
        "same_sender_boot": bool(boots) and all(
            type(boot) is int and 0 <= boot <= 65535 and boot == boots[0] for boot in boots
        ),
        "sequences_advance": len(sequences) >= 2 and all(
            type(sequence) is int and 0 <= sequence <= 65535 for sequence in sequences
        ) and all(0 < (current - previous) % 65536 < 32768
                  for previous, current in zip(sequences, sequences[1:])),
        "save_and_exit": end.get("reason") == "save_and_exit",
        "received_count_matches": type(count) is int and count == len(packets),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="1홉 JSONL의 최신 시험 세션을 로컬에서 검사합니다.")
    parser.add_argument("log", type=Path, help="폰에서 내보낸 JSONL 파일")
    args = parser.parse_args(argv)
    try:
        with args.log.open(encoding="utf-8") as log:
            result = check_session(latest_session(log))
    except (OSError, UnicodeError):
        print("UTF-8 로그 파일을 읽지 못했습니다.", file=sys.stderr)
        return 2
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if all(passed for name, passed in result.items() if name != "received") else 1


if __name__ == "__main__":
    raise SystemExit(main())
