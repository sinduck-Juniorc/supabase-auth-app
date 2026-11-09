import os
for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
from pathlib import Path
import json
import time
import tracemalloc
import pickle
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from policies.chebyshev import LOW, HIGH, FEATURES, PAIRS, design, normalize, reference_quality, clenshaw, QualityModel
from simulator.runtime import ROOT, actual_environment


def dataset(seed, size):
    rng = np.random.default_rng(seed)
    x = rng.uniform(LOW, HIGH, (size, 6))
    y = reference_quality(x)
    return x, y


def scores(y, predicted):
    error = y - np.clip(predicted, 0, 1)
    return {"mae": float(np.mean(np.abs(error))), "rmse": float(np.sqrt(np.mean(error**2))),
            "max_abs_error": float(np.max(np.abs(error)))}


def main():
    out = ROOT / "models"
    out.mkdir(exist_ok=True)
    pairs = [dataset(seed, 3000) for seed in (100, 101, 102, 103)]
    x = np.concatenate([v[0] for v in pairs])
    y = np.concatenate([v[1] for v in pairs])
    valid_x, valid_y = dataset(150, 3000)
    test_x, test_y = dataset(160, 3000)
    models, rows, coefficients = {}, [], {}
    fits = {}
    for degree in (3, 5, 7):
        start = time.perf_counter()
        coef = np.linalg.lstsq(design(x, degree), y, rcond=None)[0]
        coefficients[str(degree)] = coef.tolist()
        fits[f"cheb_{degree}"] = time.perf_counter() - start
        rows.append({"model": f"cheb_{degree}", "split": "validation", **scores(valid_y, design(valid_x, degree) @ coef)})
    # 고정 규칙: 검증 RMSE 최소, 동점이면 낮은 차수.
    selected = min(rows, key=lambda r: (r["rmse"], int(r["model"].split("_")[1])))
    degree = int(selected["model"].split("_")[1])
    selected_coef = coefficients[str(degree)]
    tables = []
    for feature in range(6):
        coef = [0.] + selected_coef[1 + feature * degree:1 + (feature + 1) * degree]
        tables.append([clenshaw(float(z), coef) for z in np.linspace(-1, 1, 33)])
    document = {"selected_degree": degree, "features": list(FEATURES), "cheb": coefficients, "lut": tables,
                "training_seeds": [100, 101, 102, 103], "validation_seeds": [150], "test_seeds": [160],
                "reference": "합성 예상 유용도 함수에 대한 회귀; RF 실측·RL teacher·TTFF 학습 아님",
                "selection_rule": "검증 RMSE 최소; 같은 오차면 낮은 차수"}
    (out / "quality.json").write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
    quality = QualityModel(out / "quality.json")
    for d in (3, 5, 7):
        models[f"cheb_{d}"] = lambda v, d=d: quality.predict(v, d)
    models["lut"] = quality.lut
    estimators = {"linear": LinearRegression(), "tree": DecisionTreeRegressor(max_depth=8, min_samples_leaf=20, random_state=100),
                  "mlp": MLPRegressor(hidden_layer_sizes=(16, 8), max_iter=1000, early_stopping=True,
                                     n_iter_no_change=20, random_state=100, tol=1e-6)}
    estimator_bytes = {}
    for name, estimator in estimators.items():
        start = time.perf_counter()
        estimator.fit(normalize(x), y)
        fits[name] = time.perf_counter() - start
        models[name] = lambda v, e=estimator: float(np.clip(e.predict(normalize(v).reshape(1, -1))[0], 0, 1))
        # 참조 구현 크기. MCU Flash/RAM 측정값으로 해석하지 않는다.
        estimator_bytes[name] = len(pickle.dumps(estimator))
    bench_rows = []
    for name, predict in models.items():
        prediction = np.array([predict(v) for v in test_x])
        row = {"model": name, "split": "test", **scores(test_y, prediction), "fit_s": fits.get(name, fits[f"cheb_{degree}"])}
        samples = test_x[:300]
        for repeat in range(5):
            start = time.perf_counter_ns()
            for v in samples:
                predict(v)
            ns = (time.perf_counter_ns() - start) / len(samples)
            bench_rows.append({"model": name, "repeat": repeat, "scalar_inference_ns": ns})
        row["median_inference_us"] = float(np.median([r["scalar_inference_ns"] for r in bench_rows if r["model"] == name]) / 1000)
        tracemalloc.start()
        predict(samples[0])
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        row["python_peak_allocation_bytes"] = peak
        if name.startswith("cheb"):
            row["float64_coefficient_bytes"] = len(coefficients[name.split("_")[1]]) * 8
        elif name == "lut":
            row["float64_coefficient_bytes"] = (6 * 33 + 16) * 8
        else:
            row["python_pickle_bytes"] = estimator_bytes[name]
        row["mcu_flash_bytes"] = None
        row["mcu_inference_energy_j"] = None
        rows.append(row)
    pd.DataFrame(rows).to_csv(out / "model_comparison.csv", index=False)
    pd.DataFrame(bench_rows).to_csv(out / "inference_timing_raw.csv", index=False)
    data_rows = []
    for split, seeds in [("train", (100, 101, 102, 103)), ("validation", (150,)), ("test", (160,))]:
        for seed in seeds:
            features, labels = dataset(seed, 3000)
            frame = pd.DataFrame(features, columns=FEATURES)
            frame["target"] = labels
            frame["seed"], frame["split"] = seed, split
            data_rows.append(frame)
    pd.concat(data_rows).to_csv(out / "regression_data.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    (out / "training_manifest.json").write_text(json.dumps({"environment": actual_environment(), "train_samples": len(x),
        "test_samples": len(test_x), "validation_samples": len(valid_x), "selected_degree": degree,
        "command": "python -m training.fit_quality"}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(pd.DataFrame([r for r in rows if r["split"] == "test"]).to_string(index=False))
    print(f"검증 집합으로 선택한 차수: {degree}")


if __name__ == "__main__":
    main()
