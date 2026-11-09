import os
# spawn된 자식과 수치 라이브러리의 중첩 병렬화를 제한한다.
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "1"
import argparse
import concurrent.futures
import json
import multiprocessing
from pathlib import Path
import sys
import time
import zipfile
import pandas as pd
import yaml
from simulator.network import Simulation
from simulator.metrics import metrics
from simulator.runtime import ROOT, actual_environment, source_version, MemorySampler
from policies.combined import POLICIES


def run_one(job):
    config, policy, seed, version, environment_id = job
    start = time.perf_counter()
    with MemorySampler() as sampler:
        sim = Simulation(config, policy, seed).run()
        result, nodes = metrics(sim)
    result.update(wall_s=time.perf_counter() - start, peak_rss_bytes=sampler.peak,
                  peak_rss_sampling_s=.02, code_version=version, actual_environment_id=environment_id)
    for row in nodes:
        row.update(scenario=config["scenario"], policy=policy, seed=seed)
    for row in sim.requests:
        row.update(scenario=config["scenario"], policy=policy, seed=seed)
    return result, nodes, sim.requests, dict(sim.event_counts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", nargs="+", default=[str(p) for p in sorted((ROOT / "configs").glob("50nodes_*.yaml"))])
    parser.add_argument("--policy", nargs="+", choices=POLICIES, default=list(POLICIES))
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--seed-start", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--phase", choices=("smoke", "tuning", "evaluation", "sensitivity"), default="evaluation")
    parser.add_argument("--nodes", type=int)
    parser.add_argument("--out", type=Path, default=ROOT / "outputs/evaluation")
    args = parser.parse_args()
    if args.seeds < 1 or args.workers < 1:
        parser.error("시드와 프로세스 수는 양수")
    if args.phase == "evaluation" and (args.seeds < 30 or args.seed_start < 1000 or args.nodes not in (None, 50)):
        parser.error("본 평가는 50노드, 1000 이상 독립 시드 최소 30개")
    if args.phase == "evaluation" and not (ROOT / "reports/preregistration.json").exists():
        parser.error("평가 전에 튜닝 자료로 기준선과 QoS를 고정해야 합니다")
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / "runs.csv").exists():
        parser.error("기존 실행 디렉터리입니다. 새 --out을 사용하세요")
    env = actual_environment()
    configs = [yaml.safe_load(Path(p).read_text(encoding="utf-8")) for p in args.config]
    for config in configs:
        if args.nodes is not None:
            config["nodes"] = args.nodes
        if args.phase == "evaluation" and config["nodes"] != 50:
            parser.error("본 평가 노드 수는 50")
    version = source_version()
    # 실행 당시 코드를 함께 보존하므로 이후 보고서 도구 수정과도 구분할 수 있다.
    with zipfile.ZipFile(args.out / "source_snapshot.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for pattern in ("**/*.py", "configs/*.yaml", "requirements*.txt", "models/quality.json", "reports/*registration*.json", "reports/evaluation_design_ko.md"):
            for file in sorted(ROOT.glob(pattern)):
                if "outputs" not in file.relative_to(ROOT).parts:
                    archive.write(file, file.relative_to(ROOT))
    manifest = {"command": sys.argv, "phase": args.phase, "workers": args.workers,
                "code_version": version, "actual_environment": env, "configs": configs,
                "seeds": list(range(args.seed_start, args.seed_start + args.seeds)),
                "policies": args.policy, "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    jobs = [(config, policy, seed, version, env["environment_id"]) for config in configs
            for seed in manifest["seeds"] for policy in args.policy]
    results, nodes, requests, counts = [], [], [], []
    start = time.perf_counter()
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers, mp_context=multiprocessing.get_context("spawn")) as executor:
        for index, data in enumerate(executor.map(run_one, jobs, chunksize=1), 1):
            result, node_rows, request_rows, event_counts = data
            results.append(result)
            nodes.extend(node_rows)
            requests.extend(request_rows)
            counts.append({"scenario": result["scenario"], "policy": result["policy"], "seed": result["seed"], **event_counts})
            print(f"[{index}/{len(jobs)}] {result['scenario']} {result['policy']} seed={result['seed']} E={result['energy_j']:.4f}J success={result['success_rate']:.4f} events={result['events']} wall={result['wall_s']:.3f}s", flush=True)
            if index % 24 == 0:
                pd.DataFrame(results).to_csv(args.out / "checkpoint_runs.csv", index=False)
    pd.DataFrame(results).to_csv(args.out / "runs.csv", index=False)
    pd.DataFrame(nodes).to_csv(args.out / "nodes.csv", index=False)
    pd.DataFrame(requests).to_csv(args.out / "requests.csv", index=False)
    pd.DataFrame(counts).fillna(0).to_csv(args.out / "event_counts.csv", index=False)
    manifest.update(wall_s=time.perf_counter() - start, runs=len(results),
                    completed_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (args.out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"실행 종료: {len(results)}회, 벽시계 {manifest['wall_s']:.2f}s", flush=True)


if __name__ == "__main__":
    main()
