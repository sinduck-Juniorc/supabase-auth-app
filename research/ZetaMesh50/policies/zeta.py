import numpy as np


def rank_probabilities(count, exponent=1.4, exploration=.10):
    if count < 0 or not np.isfinite(exponent) or exponent < 0 or not 0 < exploration <= 1:
        raise ValueError("잘못된 제타 설정")
    if count == 0:
        return np.empty(0)
    weight = np.arange(1, count + 1, dtype=float) ** (-exponent)
    return (1 - exploration) * weight / weight.sum() + exploration / count
