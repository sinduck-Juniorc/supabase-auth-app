import argparse
import json
from pathlib import Path
import subprocess
import sys
import yaml
from simulator.runtime import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    design = json.loads((ROOT / "reports/preregistration.json").read_text(encoding="utf-8"))
    directory = ROOT / "configs/sensitivity"
    directory.mkdir(exist_ok=True)
    for scenario, details in design["choices"].items():
        config = yaml.safe_load((ROOT / f"configs/50nodes_{scenario}.yaml").read_text(encoding="utf-8"))
        variants = {"donors": {"donor_fraction": .2 if config["donor_fraction"] == .1 else .1},
                    "lifetime": {"packet_lifetime_s": 12.}, "nlos": {"nlos_loss_db": config["nlos_loss_db"] + 6}}
        for variant, changes in variants.items():
            path = directory / f"{scenario}_{variant}.yaml"
            path.write_text(yaml.safe_dump({**config, **changes}, allow_unicode=True, sort_keys=False), encoding="utf-8")
            out = ROOT / f"outputs/sensitivity/{scenario}_{variant}"
            command = [sys.executable, "-m", "scripts.run_experiment", "--config", str(path), "--phase", "sensitivity",
                       "--seed-start", "3000", "--seeds", "5", "--workers", str(args.workers),
                       "--policy", details["baseline"], "combined", "--out", str(out)]
            print("실행:", " ".join(command), flush=True)
            subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
