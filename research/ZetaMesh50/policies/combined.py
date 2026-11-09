from dataclasses import dataclass
import math
import random
from .chebyshev import QualityModel
from .zeta import rank_probabilities

POLICIES = ("fixed", "random", "greedy", "zeta_only", "cheb_only", "combined", "threshold", "lut")


@dataclass(frozen=True)
class Observation:
    node_id: int
    last_seen: float
    rssi_dbm: float
    battery: float
    created_at: float
    expires_at: float
    hops: int
    p_rx: float
    gnss_quality: float

    def features(self, time):
        raw = [self.rssi_dbm, self.battery, max(0, time - self.created_at),
               self.hops, self.p_rx, self.gnss_quality]
        defaults = [-100., .2, 30., 5., .1, .1]
        return [float(v) if isinstance(v, (int, float)) and math.isfinite(v) else default
                for v, default in zip(raw, defaults)]


class Policy:
    def __init__(self, name, seed, node, config, model=None):
        if name not in POLICIES:
            raise ValueError(name)
        self.name = name
        self.rng = random.Random((seed + 1) * 100003 + node * 101 + POLICIES.index(name))
        self.config = config
        self.model = model

    def score(self, candidate, time):
        features = candidate.features(time)
        if self.name in ("cheb_only", "combined"):
            return self.model.predict(features)
        if self.name == "lut":
            return self.model.lut(features)
        rssi, battery, age, hops, p_rx, quality = features
        return (.30 * p_rx + .25 * quality + .20 * max(0, 1 - age / 30) +
                .15 * battery + .10 * max(0, 1 - hops / 5))

    def choose(self, observed, time):
        # 이 함수에는 노드/좌표/실제 링크 행렬 접근권이 없다.
        candidates = [c for c in observed if time - c.last_seen <= self.config["cache_s"] and
                      c.created_at <= time < c.expires_at and c.hops < self.config["max_hops"]]
        if not candidates:
            return None
        if self.name == "fixed":
            return min(candidates, key=lambda c: c.node_id).node_id
        if self.name == "random":
            return self.rng.choice(candidates).node_id
        ordered = sorted(candidates, key=lambda c: (-self.score(c, time), c.node_id))
        if self.name in ("zeta_only", "combined"):
            # 상태 기반 지수: 가장 좋은 관측 품질이 높을 때 이용 비중을 증가.
            exponent = 1 + min(1, max(0, self.score(ordered[0], time)))
            probabilities = rank_probabilities(len(ordered), exponent, self.config["exploration"])
            return self.rng.choices([x.node_id for x in ordered], probabilities, k=1)[0]
        return ordered[0].node_id

    def schedule(self, has_fresh, pending, has_candidates):
        # 후보가 없으면 모든 정책의 공통 초기 탐색으로 복귀한다.
        adaptive = self.name in ("combined", "threshold", "lut")
        save = adaptive and has_fresh and not pending and has_candidates
        window = self.config["low_scan_window_s"] if save else self.config["base_scan_window_s"]
        adv = self.config["slow_adv_s"] if save else self.config["base_adv_s"]
        if self.name == "random":
            adv *= self.rng.uniform(.8, 1.2)
        return (min(self.config["max_scan_window_s"], max(self.config["min_scan_window_s"], window)),
                min(self.config["max_adv_s"], max(self.config["min_adv_s"], adv)))

    def cpu_cost(self, candidates):
        # ESP32 미실측 가정: 공통 80us + 후보별 단순 1us / 체비쇼프 6us / LUT 2us.
        cost = 6e-6 if self.name in ("combined", "cheb_only") else (2e-6 if self.name == "lut" else 1e-6)
        return 80e-6 + cost * candidates
