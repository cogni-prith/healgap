"""One heal run. Usage: python scripts/run_heal.py --config configs/arm_filter_rule.yaml --seed 0

The arm YAML names a base profile YAML (key `base`) and adds the `arm` section.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import yaml

from healgap.detectors.rule import d_rule
from healgap.env.dataset import load_dataset
from healgap.eval.heal_eval import make_evaluator
from healgap.eval.oracle_detectors import make_oracle, make_sim
from healgap.loop import manifest
from healgap.loop.heal import HealConfig, run_heal

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--run-dir", type=Path, default=None, help="resume an existing run directory")
    args = ap.parse_args()
    arm_yaml = yaml.safe_load(args.config.read_text())
    raw = {**yaml.safe_load((args.config.parent / arm_yaml["base"]).read_text()), "arm": arm_yaml["arm"]}
    if raw["arm"]["detector"] == "sim" and raw["arm"].get("sim_recall") is None:
        # D_sim is matched to D_rule's measured round-0 recall and false-positive rate (scripts/calibrate_sim.py)
        cal = json.loads(Path("runs", f"sim_calibration_{raw['label']}.json").read_text())
        raw["arm"] = {**raw["arm"], "sim_recall": cal["sim_recall"], "sim_fpr": cal["sim_fpr"]}
    cfg = HealConfig.from_dict(raw)
    ds = load_dataset(cfg.profile)
    detectors = {
        "none": lambda ep: 0,
        "rule": d_rule,
        "oracle": make_oracle(ds),
        "sim": make_sim(ds, cfg.arm.sim_recall or 0.0, cfg.arm.sim_fpr or 0.0, args.seed),
    }
    flag = detectors[cfg.arm.detector]
    run_dir = args.run_dir or Path("runs") / f"heal_{cfg.label}_{cfg.arm.name}_seed{args.seed}_{time.strftime('%Y%m%dT%H%M%S')}"
    man = manifest.start(run_dir, raw, args.seed, cfg.model_id, cfg.label)
    status = "failed"
    try:
        run_heal(cfg, args.seed, run_dir, flag, make_evaluator(ds, run_dir, args.seed, flag), cache_dir=Path("runs") / "_base_cache")
        status = "completed"
    finally:
        manifest.finish(run_dir, man, status)
        print(f"[heal] status={status} run_dir={run_dir}")
