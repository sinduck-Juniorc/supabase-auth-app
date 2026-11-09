from collections import defaultdict


class EnergyLedger:
    """무선 상태는 상호 배타적. CPU 증분 전력과 독립 GNSS 모듈만 가산한다."""
    def __init__(self, config):
        self.config = config
        self.last = 0.0
        self.tx = 0
        self.rx = 0
        self.scanning = False
        self.awake = False
        self.gnss = False
        self.seconds = defaultdict(float)
        self.cpu_seconds = 0.0

    @property
    def state(self):
        if self.tx:
            return "tx"
        if self.rx:
            return "rx"
        if self.scanning:
            return "scan"
        return "idle" if self.awake else "sleep"

    def account(self, time):
        delta = time - self.last
        if delta < -1e-9:
            raise ValueError("시간 역행")
        self.seconds[self.state] += max(0.0, delta)
        if self.gnss:
            self.seconds["gnss"] += max(0.0, delta)
        self.last = time

    def cpu(self, seconds):
        if seconds < 0:
            raise ValueError("음수 CPU 시간")
        self.cpu_seconds += seconds

    def components(self):
        voltage = self.config["voltage_v"]
        result = {state + "_j": voltage * self.config[state + "_a"] *
                  self.seconds[state] for state in ("tx", "rx", "scan", "idle", "sleep", "gnss")}
        result["cpu_j"] = voltage * self.config["cpu_increment_a"] * self.cpu_seconds
        return result

    def total(self):
        return sum(self.components().values())
