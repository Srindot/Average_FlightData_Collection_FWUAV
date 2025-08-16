import os
import csv
import logging
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.stats import qmc

# --- Sweep Configuration ---
class SweepConfig:
    def __init__(self, param_grid, n_samples=10, max_workers=2, chunk_size=5, out_file="sweep_results.csv"):
        self.param_grid = param_grid
        self.n_samples = n_samples
        self.max_workers = max_workers
        self.chunk_size = chunk_size
        self.out_file = out_file

# --- Latin Hypercube Sampling ---
def lhs_samples(param_grid, n_samples):
    continuous_params = {k: v for k, v in param_grid.items() if isinstance(v, tuple)}
    categorical_params = {k: v for k, v in param_grid.items() if isinstance(v, list)}

    if continuous_params:
        sampler = qmc.LatinHypercube(d=len(continuous_params))
        sample = sampler.random(n=n_samples)
        lhs_scaled = qmc.scale(
            sample,
            [v[0] for v in continuous_params.values()],
            [v[1] for v in continuous_params.values()]
        )
    else:
        lhs_scaled = np.zeros((n_samples, 0))

    samples = []
    for i in range(n_samples):
        s = {}
        for j, key in enumerate(continuous_params.keys()):
            s[key] = lhs_scaled[i, j]
        for key, choices in categorical_params.items():
            s[key] = np.random.choice(choices)
        samples.append(s)
    return samples

# --- Worker Function (Replace with Solver) ---
def _worker(params):
    try:
        # Replace this section with the real solver call
        # Example dummy computation
        drag = params.get("AoA", 0) * 0.1
        lift = params.get("flapping_period", 1) * 2.0
        velocity = params.get("velocity", 0)
        return {
            "status": "ok",
            **params,
            "drag": drag,
            "lift": lift,
            "efficiency": lift / (drag + 1e-6),
            "momentum": velocity * lift
        }
    except Exception as e:
        return {"status": "error", **params, "error": str(e)}

# --- Main Sweep Runner ---
def run_sweep(cfg: SweepConfig):
    combos = lhs_samples(cfg.param_grid, cfg.n_samples)
    results, ok_count, err_count = [], 0, 0

    with ProcessPoolExecutor(max_workers=cfg.max_workers) as ex:
        for idx, rec in enumerate(ex.map(_worker, combos), 1):
            results.append(rec)

            if rec["status"] == "ok":
                ok_count += 1
            else:
                err_count += 1

            if len(results) >= cfg.chunk_size:
                _flush_results(cfg.out_file, results)
                results = []

            if idx % 5 == 0:
                logging.info("Progress: %d/%d runs complete", idx, cfg.n_samples)

    if results:
        _flush_results(cfg.out_file, results)

    logging.info("Sweep finished: %d ok, %d errors", ok_count, err_count)

# --- Write to CSV ---
def _flush_results(out_file, records):
    write_header = not os.path.exists(out_file)
    with open(out_file, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        if write_header:
            writer.writeheader()
        writer.writerows(records)

# --- Example Usage ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    param_grid = {
        "AoA": (10, 30),
        "flapping_period": (0.65, 0.85),
        "velocity": (3, 5),
        "airfoil": ["naca2412", "naca0012"]
    }

    cfg = SweepConfig(
        param_grid=param_grid,
        n_samples=20,
        max_workers=4,
        chunk_size=10
    )

    run_sweep(cfg)
