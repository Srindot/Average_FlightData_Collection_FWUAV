#!/usr/bin/env python3
"""
Safe parallel sweep with LHS sampling and immediate CSV write per process,
balanced across airfoils, with lift filtering.
"""
from __future__ import annotations

import os
import csv
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Sequence, Tuple, Optional

import numpy as np
from concurrent.futures import ProcessPoolExecutor, as_completed
from scipy.stats import qmc

from simulation import simulation  

# --- Constants ---

DEFAULT_OUTPUT = "Data/AverageFlightData10.csv"
DEFAULT_ERROR_CSV = "Data/AverageFlightData10_errors.csv"
DEFAULT_LOG = "logs/mark4_sweep.log"

CSV_COLUMNS = [
    "airfoil", "wingspan", "aspect_ratio", "taper_ratio",
    "flapping_period", "air_speed", "angle_of_attack",
    "lift", "induced_drag", "status", "error"
]

ARG_ORDER = [
    "airfoil", "wingspan", "aspect_ratio", "taper_ratio",
    "flapping_period", "air_speed", "angle_of_attack"
]

VALID_AIRFOILS = ["naca8304", "goe225", "naca2412", "naca0012"]

# --- Config Dataclass ---

@dataclass(frozen=True)
class SweepConfig:
    param_grid: Dict[str, Sequence[Any]]
    n_samples: int = 20
    output_csv: str = DEFAULT_OUTPUT
    error_csv: str = DEFAULT_ERROR_CSV
    log_path: str = DEFAULT_LOG
    max_workers: Optional[int] = 2

# --- Utilities ---

def setup_logging(log_path: str) -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        filemode="a",   # ✅ append instead of overwrite
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.getLogger().addHandler(console)

def ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

def _validate_and_split_params(param_grid: Dict[str, Sequence[Any]], order: Sequence[str]):
    continuous_keys, bounds, constant_map, categorical_map = [], [], {}, {}
    for k in order:
        vals = param_grid[k]
        if isinstance(vals, tuple) and len(vals) == 2 and all(isinstance(v, (int, float)) for v in vals):
            lo, hi = vals
            if lo < hi:
                continuous_keys.append(k)
                bounds.append((lo, hi))
            else:
                constant_map[k] = lo
        elif isinstance(vals, (list, tuple)) and len(vals) >= 2 and all(isinstance(v, (int, float)) for v in vals):
            lo, hi = min(vals), max(vals)
            if lo < hi:
                continuous_keys.append(k)
                bounds.append((lo, hi))
            else:
                constant_map[k] = lo
        else:
            if isinstance(vals, (list, tuple)):
                categorical_map[k] = list(vals)
            else:
                constant_map[k] = vals
    return continuous_keys, bounds, constant_map, categorical_map

def lhs_samples(param_grid: Dict[str, Sequence[Any]], order: Sequence[str], n_samples: int) -> List[Tuple[Any, ...]]:
    continuous_keys, bounds, constant_map, categorical = _validate_and_split_params(param_grid, order)
    if continuous_keys:
        sampler = qmc.LatinHypercube(d=len(continuous_keys))
        r = sampler.random(n=n_samples)
        lo_bounds = [b[0] for b in bounds]
        hi_bounds = [b[1] for b in bounds]
        scaled = qmc.scale(r, lo_bounds, hi_bounds)
    else:
        scaled = np.zeros((n_samples, 0))
    samples = []
    for i in range(n_samples):
        rec = {}
        for j, key in enumerate(continuous_keys):
            rec[key] = float(scaled[i, j])
        for key, val in constant_map.items():
            rec[key] = val
        for key, opts in categorical.items():
            rec[key] = opts[0] if len(opts) == 1 else np.random.choice(opts)
        samples.append(tuple(rec[name] for name in order))
    return samples

def _worker(args: Tuple[Any, ...]) -> Dict[str, Any]:
    airfoil, wingspan, aspect_ratio, taper_ratio, fp, va, aoa = args
    if airfoil not in VALID_AIRFOILS:
        return {
            "airfoil": airfoil, "wingspan": wingspan, "aspect_ratio": aspect_ratio, "taper_ratio": taper_ratio,
            "flapping_period": fp, "air_speed": va, "angle_of_attack": aoa,
            "lift": None, "induced_drag": None,
            "status": "error",
            "error": "Airfoil not in database!"
        }
    base = {
        "airfoil": airfoil, "wingspan": wingspan, "aspect_ratio": aspect_ratio, "taper_ratio": taper_ratio,
        "flapping_period": fp, "air_speed": va, "angle_of_attack": aoa,
        "lift": None, "induced_drag": None
    }
    try:
        lift, drag = simulation(
            mw_airfoil=airfoil, fp=fp, va=va, aoa=aoa,
            mw_wingspan=wingspan, aspect_ratio=aspect_ratio, taper_ratio=taper_ratio
        )
        if lift is None:
            raise ValueError("Simulation returned None for lift")

        # --- ✅ Lift filtering: skip if lift < -100 N ---
        if lift < -100.0:
            base["status"] = "skipped"
            base["error"] = f"Extreme negative lift (lift={lift:.2f} N)"
            return base

        base["lift"] = float(lift)
        base["induced_drag"] = float(drag) if drag is not None else None
        base["status"] = "ok"
        base["error"] = ""
    except Exception as e:
        base["status"] = "error"
        base["error"] = f"{type(e).__name__}: {e}"
    return base

def _write_frame(df_rows: List[Dict[str, Any]], path: str) -> None:
    ensure_parent_dir(path)
    if not df_rows:
        return
    write_header = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerows(df_rows)

# --- Main sweep ---

def run_sweep(cfg: SweepConfig) -> None:
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
    setup_logging(cfg.log_path)

    all_airfoils = cfg.param_grid.get("airfoil", [])
    if not all_airfoils:
        raise ValueError("No airfoils provided in param_grid")

    # --- Generate samples for all airfoils ---
    sampling_grid = {k: v for k, v in cfg.param_grid.items() if k != "airfoil"}
    samples = []
    for airfoil in all_airfoils:
        grid_for_airfoil = dict(sampling_grid)
        grid_for_airfoil["airfoil"] = [airfoil]
        samples.extend(lhs_samples(grid_for_airfoil, ARG_ORDER, cfg.n_samples))

    total = len(samples)
    logging.info("Prepared %d samples for sweep (%d per airfoil)", total, cfg.n_samples)

    max_workers = cfg.max_workers or max(1, os.cpu_count())
    ok_count = err_count = skip_count = 0
    start_time = time.time()

    # --- ✅ Submit ALL tasks at once ---
    with ProcessPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_worker, s): s for s in samples}

        for fut in as_completed(futures):
            params = futures[fut]
            try:
                rec = fut.result()
            except Exception as e:
                rec = dict(zip(ARG_ORDER, params))
                rec.update({"lift": None, "induced_drag": None, "status": "error", "error": str(e)})

            if rec.get("status") == "ok":
                ok_count += 1
                _write_frame([rec], cfg.output_csv)
            elif rec.get("status") == "skipped":
                skip_count += 1
                logging.info("Skipped: %s", rec.get("error"))
            else:
                err_count += 1
                _write_frame([rec], cfg.error_csv)
                logging.error("Task failed: %s", rec.get("error", "<no error>"))

            logging.info("Progress: %d/%d (ok=%d, skipped=%d, err=%d)", 
                         ok_count+skip_count+err_count, total, ok_count, skip_count, err_count)

    logging.info("Sweep complete in %.1fs — ok=%d, skipped=%d, errors=%d", 
                 time.time()-start_time, ok_count, skip_count, err_count)

# --- Entrypoint ---

def default_param_grid() -> Dict[str, Sequence[Any]]:
    return {
        "airfoil": VALID_AIRFOILS,
        "flapping_period": (0.4, 1.2),
        "angle_of_attack": (2.0, 30.0),
        "air_speed": (3.0, 5.0),
        "wingspan": (0.4, 1.2),
        "aspect_ratio": (1.25, 4.0),
        "taper_ratio": (0.2, 0.6)
    }

def main() -> None:
    cfg = SweepConfig(param_grid=default_param_grid(), n_samples=20, max_workers=5)
    run_sweep(cfg)

if __name__ == "__main__":
    main()
