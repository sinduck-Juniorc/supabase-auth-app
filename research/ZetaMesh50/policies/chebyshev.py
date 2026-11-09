"""학습된 다변수 가산형 품질 함수. T3 양자화 코덱과 무관하다."""
from pathlib import Path
import json
import math
import numpy as np

FEATURES = ("rssi_dbm", "battery", "age_s", "hops", "p_rx", "gnss_quality")
LOW = np.array([-100., 0., 0., 0., 0., 0.])
HIGH = np.array([-35., 1., 30., 5., 1., 1.])
DEFAULT = np.array([-100., .2, 30., 5., .1, .1])
PAIRS = [(a, b) for a in range(6) for b in range(a + 1, 6)]


def normalize(values):
    x = np.asarray(values, dtype=float)
    x = np.where(np.isfinite(x), x, DEFAULT)
    return 2 * (np.clip(x, LOW, HIGH) - LOW) / (HIGH - LOW) - 1


def clenshaw(x, coefficients):
    b1, b2 = 0., 0.
    for value in reversed(coefficients[1:]):
        b0 = 2 * x * b1 - b2 + value
        b2, b1 = b1, b0
    return x * b1 - b2 + coefficients[0]


def design(x, degree):
    z = normalize(x)
    columns = [np.ones(len(z))]
    for j in range(6):
        vander = np.polynomial.chebyshev.chebvander(z[:, j], degree)
        columns.extend(vander[:, k] for k in range(1, degree + 1))
    columns.extend(z[:, a] * z[:, b] for a, b in PAIRS)
    return np.column_stack(columns)


class QualityModel:
    def __init__(self, path=None):
        path = Path(path) if path else Path(__file__).resolve().parents[1] / "models/quality.json"
        self.data = json.loads(path.read_text(encoding="utf-8"))
        self.degree = self.data["selected_degree"]
        self.coefficients = self.data["cheb"][str(self.degree)]

    def predict(self, values, degree=None):
        degree = degree or self.degree
        coef = self.data["cheb"][str(degree)]
        z = normalize(values)
        if z.ndim != 1:
            return np.clip(design(values, degree) @ np.asarray(coef), 0, 1)
        value = coef[0]
        at = 1
        for feature in z:
            value += clenshaw(float(feature), [0.] + coef[at:at + degree])
            at += degree
        value += sum(coef[at + k] * z[a] * z[b] for k, (a, b) in enumerate(PAIRS))
        return float(np.clip(value, 0, 1))

    def lut(self, values):
        z = normalize(values)
        table = self.data["lut"]
        size = len(table[0])
        result = self.coefficients[0]
        for j, feature in enumerate(z):
            u = (float(feature) + 1) / 2 * (size - 1)
            index = min(int(u), size - 2)
            fraction = u - index
            result += table[j][index] * (1 - fraction) + table[j][index + 1] * fraction
        at = 1 + 6 * self.degree
        result += sum(self.coefficients[at + k] * z[a] * z[b] for k, (a, b) in enumerate(PAIRS))
        return float(np.clip(result, 0, 1))


def reference_quality(values):
    # 미보정 합성 회귀 목표. 실제 GNSS 품질/전달률의 정답이라고 주장하지 않는다.
    x = np.clip(np.where(np.isfinite(values), values, DEFAULT), LOW, HIGH)
    rssi, battery, age, hops, p_rx, quality = x.T
    link = 1 / (1 + np.exp(-(rssi + 83) / 6))
    return ((.5 * link + .5 * p_rx) * (.35 + .65 * quality) *
            np.exp(-age / 18) * (.4 + .6 * battery) / (1 + .15 * hops))
