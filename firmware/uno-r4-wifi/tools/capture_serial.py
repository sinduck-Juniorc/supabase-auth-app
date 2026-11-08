"""실제 연결된 R4의 JSONL 로그를 수집한다. 예시 데이터를 생성하지 않는다."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import platform
import re
import sys
import time

EVENTS = {"boot", "status", "generated_virtual", "advertise_update", "received_virtual", "relay_queued",
          "ble_ready", "ble_init_failed", "mode_advertise", "mode_scan", "scan_failed", "advertise_failed",
          "radio_stopped", "exploration_fallback", "expired", "invalid_frame", "hop_limit", "role_changed",
          "advertisement_too_large", "help"}

COLUMNS = ("received_utc", "elapsed_host_s", "event", "firmware", "uptime_ms", "node_id", "role", "kind",
           "source_id", "sender_id", "boot_nonce", "sequence", "source_created_ms", "age_ms",
           "lifetime_ms", "hops", "max_hops", "rssi_dbm", "gnss_quality", "battery_soc", "mode",
           "tx_updates", "rx_new", "duplicates", "invalid", "hop_drops", "expired_local", "scan_observations")


def parse_record(raw: bytes):
    if len(raw) > 1024:
        return None
    try:
        def invalid_constant(_):
            raise ValueError("유한하지 않은 JSON 숫자")
        value = json.loads(raw.decode("utf-8"), parse_constant=invalid_constant)
        if not isinstance(value, dict) or value.get("event") not in EVENTS:
            return None
        for key in ("uptime_ms", "node_id"):
            if type(value.get(key)) is not int:
                return None
        if not 0 <= value["uptime_ms"] <= 0xffffffff or not 1 <= value["node_id"] <= 250:
            return None
        if value.get("role") not in {"diagnostic", "donor", "relay", "seeker"}:
            return None
        for key in COLUMNS:
            if key in {"received_utc", "elapsed_host_s", "event", "firmware", "role", "kind", "mode"}:
                continue
            number = value.get(key)
            if number is not None and (type(number) not in (int, float) or abs(number) > 0xffffffff or not math.isfinite(number)):
                return None
        if "firmware" in value and (not isinstance(value["firmware"], str) or
                not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", value["firmware"])):
            return None
        if value.get("kind") not in (None, "virtual_gnss") or value.get("mode") not in (None, "advertise", "scan", "stopped"):
            return None
        return value
    except (UnicodeError, ValueError, TypeError, RecursionError):
        return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True, help="예: COM5")
    parser.add_argument("--seconds", type=float, default=60)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-ref", default="unknown", help="업로드한 소스의 Git 커밋 또는 빌드 식별자")
    args = parser.parse_args()
    if not 0 < args.seconds <= 86400:
        parser.error("수집 시간은 0초 초과, 24시간 이하여야 합니다.")
    try:
        import serial
    except ImportError:
        parser.exit(1, "pyserial이 필요합니다: python -m pip install -r requirements.txt\n")
    if args.out.exists():
        parser.error("기존 로그를 덮어쓰지 않습니다. 새 --out 경로를 지정하세요.")
    # 포트가 없으면 빈 결과 디렉터리를 만들지 않는다.
    try:
        device = serial.Serial(args.port, 115200, timeout=.25)
    except serial.SerialException as error:
        parser.exit(1, f"포트를 열지 못했습니다: {error}\n")
    args.out.mkdir(parents=True)
    started = time.perf_counter()
    metadata = {"port": args.port, "baud": 115200, "requested_seconds": args.seconds,
                "started_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
                "os": platform.platform(), "source_ref": args.source_ref, "rows": 0, "ignored_lines": 0,
                "device_boot_records": [], "firmware_versions": [], "energy_measured": False,
                "physical_source_verified": False, "simulated_data_generated": False}
    try:
        with device, (args.out / "serial_raw.bin").open("wb") as serial_file, \
                (args.out / "raw.jsonl").open("w", encoding="utf-8") as raw_file, \
                (args.out / "events.csv").open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=COLUMNS, extrasaction="ignore")
            writer.writeheader()
            while time.perf_counter() - started < args.seconds:
                raw = device.read_until(b"\n", size=1025)
                if not raw:
                    continue
                serial_file.write(raw)
                if not raw.endswith(b"\n"):
                    serial_file.write(device.read_until(b"\n", size=4096))
                    metadata["ignored_lines"] += 1
                    continue
                row = parse_record(raw)
                if row is None:
                    metadata["ignored_lines"] += 1
                    continue
                row["received_utc"] = datetime.now(timezone.utc).isoformat()
                row["elapsed_host_s"] = round(time.perf_counter() - started, 6)
                raw_file.write(json.dumps(row, ensure_ascii=False) + "\n")
                writer.writerow(row)
                metadata["rows"] += 1
                version = row.get("firmware")
                if isinstance(version, str) and version not in metadata["firmware_versions"]:
                    metadata["firmware_versions"].append(version)
                if row["event"] == "boot":
                    metadata["device_boot_records"].append(row)
    except KeyboardInterrupt:
        metadata["interrupted"] = True
    except serial.SerialException as error:
        metadata["serial_error"] = str(error)
        print(f"수집 중 포트 오류: {error}", file=sys.stderr)
    finally:
        metadata["wall_s"] = time.perf_counter() - started
        (args.out / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"수집 종료: {metadata['rows']}행, 무시한 줄 {metadata['ignored_lines']}개, 저장 위치 {args.out}")
    if metadata["rows"] == 0:
        parser.exit(2, "유효한 보드 로그가 없습니다. 포트·업로드·시리얼 모니터 점유 상태를 확인하세요.\n")
    if "serial_error" in metadata:
        parser.exit(3, "수집이 중단되어 일부 로그만 저장했습니다. metadata.json을 확인하세요.\n")


if __name__ == "__main__":
    main()
