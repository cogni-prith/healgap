"""Experiment 0: base rates of each exploit type before any training, under three prompt conditions.

Usage: python scripts/exp0_base_rates.py --config configs/smoke.yaml --seed 0
Eval script: it is allowed to import ground truth (hard rule 1).
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

from healgap.env.dataset import load_dataset
from healgap.env.prompts import CONDITIONS
from healgap.env.tools import SqlEnv
from healgap.eval.score import score_rows
from healgap.loop import manifest
from healgap.loop.rollout import GenConfig, collect, make_rollout_fn

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--limit", type=int, default=None, help="use only the first N train tasks (timing check)")
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS))
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    gen = GenConfig(**cfg["gen"])
    ds = load_dataset(cfg["profile"])
    tasks = sorted(ds.split("train"), key=lambda t: t.task_id)[: args.limit]

    run_dir = Path("runs") / f"exp0_{cfg['profile']}_seed{args.seed}_{time.strftime('%Y%m%dT%H%M%S')}"
    man = manifest.start(run_dir, {**cfg, "limit": args.limit, "conditions": args.conditions}, args.seed, cfg["model_id"], cfg["label"])
    status = "failed"
    summary: dict = {}
    try:
        tok = AutoTokenizer.from_pretrained(cfg["model_id"])
        model = AutoModelForCausalLM.from_pretrained(cfg["model_id"], dtype=torch.bfloat16).to("cuda").eval()
        env = SqlEnv(ds, gen.max_rows, gen.timeout_s)
        for cond in args.conditions:
            torch.manual_seed(args.seed)
            rows = collect(make_rollout_fn(env, CONDITIONS[cond], gen, model, tok), tasks, cfg["exp0"]["n_samples"], gen)
            records = score_rows(rows, ds, seed=args.seed)
            with (run_dir / f"episodes_{cond}.jsonl").open("w") as f:
                for row, rec in zip(rows, records):
                    f.write(json.dumps({**rec, "sample": row["sample"], "seconds": row["seconds"], "submitted_sql": row["episode"].submitted_sql, "conversation": row["conversation"]}, default=str) + "\n")
            n = len(records)
            summary[cond] = {
                "n_episodes": n,
                "n_tasks": len(tasks),
                "label_counts": {lab: sum(r["label"] == lab for r in records) for lab in ("OK", "E1", "E2", "E3", "E4", "E5", "ERR")},
                "hack_counts": {lab: sum(r["label"] == lab and r["W"] and not r["G"] for r in records) for lab in ("E1", "E2", "E3", "E4", "E5")},
                "weak_success": sum(r["W"] for r in records) / n,
                "true_success": sum(r["G"] for r in records) / n,
                "true_success_by_tier": {t: [sum(r["G"] for r in records if r["tier"] == t), sum(r["tier"] == t for r in records)] for t in ("easy", "medium", "hard")},
                "no_submit": sum(not r["submitted"] for r in records),
                "mean_steps": sum(r["steps"] for r in records) / n,
                "mean_seconds": sum(r["seconds"] for r in rows) / n,
            }
            (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
            print(cond, json.dumps(summary[cond]))
        status = "completed"
    finally:
        manifest.finish(run_dir, man, status, summary=summary)
        print(f"[exp0] status={status} run_dir={run_dir}")
