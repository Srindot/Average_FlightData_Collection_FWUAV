from __future__ import annotations

import os
import math
import csv
import time
import logging
from dataclasses import dataclass
from typing import Dict, Iterator, List, Sequence, Tuple, Optional, Any

import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from scipy.stats import qmc

# --- External domain code you already have ---
from avg_coeff_simulation import simulation

# ----------------------------- Configuration ---------------------------------

DEFAULT_OUTPUT = "Data/AverageFlightData10.csv"
DEFAULT_ERROR_CSV = "Data/AverageFlightData10_errors.csv"
DEFAULT_LOG = "logs/mark4_sweep.log"

CSV_COLUMNS = [
    "airfoil",
    "wingspan",
    "aspect_ratio",
    "taper_ratio",
    "flapping_period",
    "air_speed",
    "angle_of_attack",
    "lift",
    "induced_drag",
    "status",
    "error",
]

ARG_ORDER = [
    "airfoil",
    "wingspan",
    "aspect_ratio",
    "taper_ratio",
    "flapping_period",
    "air_speed",
    "angle_of_attack",
]

# ------------------------------ Data classes ---------------------------------

@dataclass(frozen=True)
class SweepConfig:
    param_grid: Dict[str, Sequence[Any]]
    n_samples: int
    output_csv: str = DEFAULT_OUTPUT
    error_csv: str = DEFAULT_ERROR_CSV
    log_path: str = DEFAULT_LOG
    max_workers: Optional[int] = None
    chunk_size: int = 0
    task_chunk_hint: Optional[int] = None

# ------------------------------ Utilities ------------------------------------

def setup_logging(log_path: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        filemode="a",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(console)

def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

def lhs_samples(param_grid: Dict[str, Sequence[Any]],
                order: Sequence[str],
                n_samples: int) -> Iterator[Tuple[Any, ...]]:
    """Generate parameter sets using Latin Hypercube Sampling."""
    continuous_keys = []
    bounds = []
    categorical_keys = {}

    for k in order:
        values = param_grid[k]
        if all(isinstance(v, (int, float)) for v in values) and len(values) > 1:
            continuous_keys.append(k)
            bounds.append([min(values), max(values)])
        else:
            categorical_keys[k] = values

    sampler = qmc.LatinHypercube(d=len(continuous_keys))
    sample = sampler.random(n=n_samples)
    scaled = qmc.scale(sample,
                       [b[0] for b in bounds],
                       [b[1] for b in bounds]) if bounds else np.zeros((n_samples,0))

    for i in range(n_samples):
        rec = {}
        for j, key in enumerate(continuous_keys):
            rec[key] = float(scaled[i, j])
        for key, values in categorical_keys.items():
            rec[key] = np.random.choice(values)
        yield tuple(rec[k] for k in order)

def _worker(args: Tuple[Any, ...]) -> Dict[str, Any]:
    (airfoil, wingspan, aspect_ratio, taper_ratio,
     flapping_period, air_speed, angle_of_attack) = args

    base: Dict[str, Any] = {
        "airfoil": airfoil,
        "wingspan": wingspan,
        "aspect_ratio": aspect_ratio,
        "taper_ratio": taper_ratio,
        "flapping_period": flapping_period,
        "air_speed": air_speed,
        "angle_of_attack": angle_of_attack,
        "lift": None,
        "induced_drag": None,
    }
    try:
        lift, induced_drag = simulation(
            mw_airfoil=airfoil,
            fp=flapping_period,
            va=air_speed,
            aoa=angle_of_attack,
            mw_wingspan=wingspan,
            aspect_ratio=aspect_ratio,
            taper_ratio=taper_ratio,
        )
        base["lift"] = float(lift) if lift is not None else None
        base["induced_drag"] = float(induced_drag) if induced_drag is not None else None
        base["status"] = "ok"
        base["error"] = ""
    except Exception as e:
        base["status"] = "error"
        base["error"] = f"{type(e).__name__}: {e}"
    return base

def _write_frame(df: pd.DataFrame, path: str, append: bool) -> None:
    ensure_parent_dir(path)
    df.to_csv(path, index=False, mode="a" if append else "w", header=not append,
              quoting=csv.QUOTE_MINIMAL)

# ------------------------------- Orchestration --------------------------------

def run_sweep(cfg: SweepConfig) -> None:
    setup_logging(cfg.log_path)

    missing = [k for k in ARG_ORDER if k not in cfg.param_grid]
    if missing:
        raise ValueError(f"param_grid missing keys: {missing}")

    workers = cfg.max_workers or os.cpu_count() or 1
    logging.info("Starting sweep: %d samples, %d workers", cfg.n_samples, workers)

    t0 = time.time()
    ok_count = err_count = wrote_rows = 0
    buffer_ok: List[Dict[str, Any]] = []
    buffer_err: List[Dict[str, Any]] = []

    for p in (cfg.output_csv, cfg.error_csv):
        if os.path.exists(p):
            os.remove(p)

    combos = lhs_samples(cfg.param_grid, ARG_ORDER, cfg.n_samples)

    with ProcessPoolExecutor(max_workers=workers) as ex:
        for rec in ex.map(_worker, combos, chunksize=cfg.task_chunk_hint or 1):
            if rec["status"] == "ok":
                ok_count += 1
                buffer_ok.append(rec)
            else:
                err_count += 1
                buffer_err.append(rec)
                logging.error("Task failed: %s", rec)

            if cfg.chunk_size and (len(buffer_ok) >= cfg.chunk_size or len(buffer_err) >= cfg.chunk_size):
                if buffer_ok:
                    _write_frame(pd.DataFrame(buffer_ok, columns=CSV_COLUMNS), cfg.output_csv, append=os.path.exists(cfg.output_csv))
                    wrote_rows += len(buffer_ok)
                    buffer_ok.clear()
                if buffer_err:
                    _write_frame(pd.DataFrame(buffer_err, columns=CSV_COLUMNS), cfg.error_csv, append=os.path.exists(cfg.error_csv))
                    buffer_err.clear()

    if buffer_ok:
        _write_frame(pd.DataFrame(buffer_ok, columns=CSV_COLUMNS), cfg.output_csv, append=os.path.exists(cfg.output_csv))
        wrote_rows += len(buffer_ok)
    if buffer_err:
        _write_frame(pd.DataFrame(buffer_err, columns=CSV_COLUMNS), cfg.error_csv, append=os.path.exists(cfg.error_csv))

    dt = time.time() - t0
    logging.info("Sweep complete in %.2fs. Results: ok=%d, errors=%d, wrote=%d rows.", dt, ok_count, err_count, wrote_rows)

# ------------------------------- Entrypoint -----------------------------------

def default_param_grid() -> Dict[str, Sequence[Any]]:
    return {
        "airfoil":        ["naca2412"],
        "flapping_period": [0.65, 0.85],
        "angle_of_attack": [10, 30],
        "air_speed":       [3, 5],
        "wingspan":        [0.4],
        "aspect_ratio":    [1.25, 3.0],
        "taper_ratio":     [0.3, 0.4],
    }

def main() -> None:
    param_grid = default_param_grid()
    cfg = SweepConfig(
        param_grid=param_grid,
        n_samples=200,   # total number of runs you want
        output_csv=DEFAULT_OUTPUT,
        error_csv=DEFAULT_ERROR_CSV,
        log_path=DEFAULT_LOG,
    )
    run_sweep(cfg)

    print("\n------------------------")
    print("Data generation complete")
    print(f"✅ Results:   {cfg.output_csv}")
    print(f"⚠️  Failures:  {cfg.error_csv} (if any)")
    print(f"📝 Log:       {cfg.log_path}")
    print("------------------------\n")

if __name__ == "__main__":
    main()