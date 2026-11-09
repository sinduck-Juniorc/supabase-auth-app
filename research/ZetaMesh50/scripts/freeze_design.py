from pathlib import Path
import hashlib
import json
import time
import pandas as pd
from simulator.runtime import ROOT


def freeze(path):
    data = pd.read_csv(path)
    if set(data.seed) != set(range(200, 205)) or set(data.nodes) != {50}:
        raise ValueError("튜닝 200~204, 50노드 자료 필요")
    baselines = ["fixed", "random", "greedy", "threshold", "lut"]
    choices = {}
    for scenario, group in data.groupby("scenario"):
        means = group.groupby("policy")[["energy_j", "success_rate", "latency_p95_s"]].mean()
        fixed = means.loc["fixed"]
        eligible = [name for name in baselines if means.loc[name, "success_rate"] >= fixed.success_rate - .02 and
                    means.loc[name, "latency_p95_s"] <= fixed.latency_p95_s * 1.05]
        chosen = min(eligible, key=lambda name: (means.loc[name, "energy_j"], baselines.index(name))) if eligible else "fixed"
        choices[scenario] = {"baseline": chosen, "eligible": eligible, "tuning_means": means.to_dict("index")}
    output = ROOT / "reports/preregistration.json"
    if output.exists():
        raise FileExistsError("기준선이 이미 고정되었습니다. 평가 뒤 덮어쓰지 않습니다")
    result = {"frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "evaluation_seeds": list(range(1000, 1030)),
              "tuning_seeds": list(range(200, 205)), "tuning_csv_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
              "design_sha256": hashlib.sha256((ROOT / "reports/evaluation_design_ko.md").read_bytes()).hexdigest(),
              "success_thresholds": {"energy_reduction_min": .10, "success_delta_min": -.02, "latency_relative_increase_max": .05},
              "choices": choices}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print({scenario: value["baseline"] for scenario, value in choices.items()})


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--tuning", type=Path, default=ROOT / "outputs/tuning/runs.csv")
    freeze(parser.parse_args().tuning)
