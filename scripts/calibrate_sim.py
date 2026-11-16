"""Set D_sim's recall and false-positive rate to D_rule's measured values at round 0.

Usage: python scripts/calibrate_sim.py --config configs/reduced.yaml --seed 0
Reads the cached train-side rollouts of the starting policy for that seed (round 1 collection and the gate set)
and writes runs/sim_calibration_<label>.json. Uses oracle labels, so it sits on the eval side.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from healgap.detectors.rule import d_rule
from healgap.env.dataset import load_dataset
from healgap.env.tools import episode_from_conversation
from healgap.eval.oracle_detectors import is_true_hack

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    ds = load_dataset(cfg["profile"])
    files = sorted(p for p in (Path("runs") / "_base_cache").glob(f"*_{cfg['profile']}_*_seeded_seed{args.seed}_*.json") if p.stem.endswith(("collect_r1", "gate")))
    assert files, "no cached starting-policy rollouts: run one heal arm for this seed first"
    eps = [episode_from_conversation(r["conversation"]) for p in files for r in json.loads(p.read_text())]
    hack = [is_true_hack(e, ds) for e in eps]
    flag = [d_rule(e) for e in eps]
    n_hack, n_clean = sum(hack), len(eps) - sum(hack)
    out = {
        "source_files": [str(p) for p in files],
        "seed": args.seed,
        "n_episodes": len(eps),
        "n_true_hacks": n_hack,
        "n_flagged": sum(flag),
        "sim_recall": sum(f for f, h in zip(flag, hack) if h) / n_hack if n_hack else 0.0,
        "sim_fpr": sum(f for f, h in zip(flag, hack) if not h) / n_clean if n_clean else 0.0,
    }
    Path("runs", f"sim_calibration_{cfg['label']}.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out))
