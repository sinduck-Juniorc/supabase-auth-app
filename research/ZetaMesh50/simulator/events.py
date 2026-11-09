from dataclasses import dataclass, field
import heapq


@dataclass(order=True)
class Event:
    time: float
    priority: int
    sequence: int
    kind: str = field(compare=False)
    data: object = field(compare=False)


class EventQueue:
    # 같은 시각: 프레임 종료 → 만료 → 요청 → 스캔 → 송신.
    PRIORITY = {"tx_end": 0, "expire": 1, "request": 2, "scan_end": 3,
                "sleep": 4, "scan_start": 5, "generate": 6,
                "gnss_end": 7, "relay": 8, "adv": 9, "tx_start": 10,
                "collision": 11, "receive": 12, "request_deadline": 13}

    def __init__(self):
        self.heap = []
        self.sequence = 0

    def push(self, time, kind, data):
        self.sequence += 1
        heapq.heappush(self.heap, Event(time, self.PRIORITY[kind], self.sequence, kind, data))

    def pop(self):
        return heapq.heappop(self.heap)

    def __bool__(self):
        return bool(self.heap)
