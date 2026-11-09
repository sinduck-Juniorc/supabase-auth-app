import hashlib
import json
import numpy as np


def environment(config, seed):
    """정책 난수와 무관한 초기 조건, 이동, 가림, 트래픽을 미리 만든다."""
    rng = np.random.default_rng(np.random.SeedSequence([seed, 8101]))
    n = config["nodes"]
    duration = config["duration_s"]
    kind = config["scenario"]
    if kind == "mountain":
        xy = np.column_stack((np.linspace(0, 650, n) + rng.normal(0, 5, n), rng.normal(0, 7, n)))
        xy[n // 2:, 0] += 65  # 단절 구간
        velocity = np.column_stack((rng.uniform(-1.2, 1.2, n), rng.uniform(-.1, .1, n)))
    elif kind == "urban":
        xy = rng.uniform(0, 240, (n, 2))
        velocity = rng.uniform(-1.5, 1.5, (n, 2))
    elif kind == "dense":
        centers = np.array([[20., 20.], [48., 35.], [35., 55.]])
        xy = centers[np.arange(n) % 3] + rng.normal(0, 9, (n, 2))
        velocity = rng.uniform(-.25, .25, (n, 2))
    else:
        raise ValueError(kind)
    donors = max(1, round(n * config["donor_fraction"]))
    roles = np.array(["Seeker"] * n, dtype=object)
    order = rng.permutation(n)
    roles[order[:donors]] = "Donor"
    roles[order[donors:donors + max(1, n // 4)]] = "Relay"
    battery = rng.uniform(.35, 1., n)
    quality = rng.uniform(.65, .98, n)
    phases = rng.uniform(0, config["scan_interval_s"], n)
    adv_phases = rng.uniform(0, config["base_adv_s"], n)
    gnss_phases = rng.uniform(0, 2, n)
    block = rng.random((n, n)) < config["nlos_probability"]
    block = np.triu(block, 1)
    block = block | block.T
    positions = np.array([xy + velocity * t for t in range(int(duration) + 2)])
    traffic = []
    for node in np.where(roles == "Seeker")[0]:
        start = config["warmup_s"] + rng.uniform(0, config["request_period_s"])
        while start + config["deadline_s"] <= duration:
            traffic.append((round(start, 6), int(node)))
            start += config["request_period_s"]
    initial = {"positions": positions.tolist(), "roles": roles.tolist(),
               "battery": battery.tolist(), "quality": quality.tolist(),
               "scan_phases": phases.tolist(), "adv_phases": adv_phases.tolist(),
               "gnss_phases": gnss_phases.tolist(), "blocked": block.tolist(), "traffic": traffic}
    fingerprint = hashlib.sha256(json.dumps(initial, sort_keys=True).encode()).hexdigest()
    return {**initial, "fingerprint": fingerprint, "positions": positions,
            "roles": roles, "battery": battery, "quality": quality, "blocked": block}
