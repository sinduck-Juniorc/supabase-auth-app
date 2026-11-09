from dataclasses import dataclass, asdict
import hashlib
import json
import math
from functools import lru_cache


@dataclass(frozen=True)
class Packet:
    version: int
    packet_id: str
    source_id: int
    message_type: str
    created_at: float
    expires_at: float
    hop_count: int
    max_hops: int
    quality_code: int
    payload_bytes: int
    integrity_tag: str = ""

    @lru_cache(maxsize=32768)
    def signed(self):
        data = asdict(self)
        data["integrity_tag"] = ""
        # 오류 검출용 체크섬. 인증 또는 암호학적 악의적 위변조 방지가 아니다.
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]

    def valid(self, now):
        try:
            ints = (self.version, self.source_id, self.hop_count, self.max_hops,
                    self.quality_code, self.payload_bytes)
            return (all(type(x) is int for x in ints) and self.version == 1 and
                    isinstance(self.packet_id, str) and 0 < len(self.packet_id) <= 64 and
                    0 <= self.source_id < 65536 and self.message_type == "virtual_gnss" and
                    math.isfinite(self.created_at) and math.isfinite(self.expires_at) and
                    0 <= self.created_at <= now < self.expires_at and
                    0 <= self.hop_count <= self.max_hops <= 8 and
                    0 <= self.quality_code <= 255 and 0 <= self.payload_bytes <= 8 and
                    self.integrity_tag == self.signed())
        except (ValueError, TypeError, OverflowError):
            return False

    def forward(self):
        if self.hop_count >= self.max_hops:
            return None
        values = asdict(self)
        values["hop_count"] += 1
        values["integrity_tag"] = ""
        new = Packet(**values)
        return Packet(**{**asdict(new), "integrity_tag": new.signed()})


def make_packet(source, sequence, now, lifetime, max_hops, quality):
    packet = Packet(1, f"{source}:{sequence}", source, "virtual_gnss", now,
                    now + lifetime, 0, max_hops, int(255 * quality), 8)
    return Packet(**{**asdict(packet), "integrity_tag": packet.signed()})


def decode_packet(data, now):
    try:
        if not isinstance(data, dict):
            return None
        packet = Packet(**data)
        return packet if packet.valid(now) else None
    except (TypeError, ValueError):
        return None
