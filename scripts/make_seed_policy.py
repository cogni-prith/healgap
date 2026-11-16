"""Seeding intervention: SFT the base model on scripted honest and exploit demonstrations over the train tasks.

Usage: python scripts/make_seed_policy.py --config configs/reduced.yaml --seed 0
Writes runs/seedpolicy_<label>_seed<seed>/adapter. Heal runs start from that adapter.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import yaml

from healgap.env.dataset import load_dataset
from healgap.env.prompts import CONDITIONS
from healgap.env.tools import SqlEnv, episode_from_conversation, make_tools
from healgap.loop import manifest
from healgap.loop.rollout import GenConfig
from healgap.loop.seeding import demo_conversation
from healgap.train.sft import SftConfig, train_sft
from healgap.verifiers.weak import v_weak

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--seed", type=int, required=True)
    args = ap.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    gen = GenConfig(**cfg["gen"])
    sft = SftConfig(**{**cfg["sft"], "lora_targets": tuple(cfg["sft"]["lora_targets"])})
    ds = load_dataset(cfg["profile"])
    env = SqlEnv(ds, gen.max_rows, gen.timeout_s)
    run_dir = Path("runs") / f"seedpolicy_{cfg['label']}_seed{args.seed}"
    man = manifest.start(run_dir, cfg, args.seed, cfg["model_id"], cfg["label"])
    status = "failed"
    try:
        rng = random.Random(f"seedpolicy-{args.seed}")
        tasks = sorted(ds.split("train"), key=lambda t: t.task_id)
        rng.shuffle(tasks)
        mix: list[str] = cfg["seeding"]["mix"]
        demos, kinds = [], []
        for i, task in enumerate(tasks):
            kind = mix[i % len(mix)]
            conv = demo_conversation(task, env, kind)
            if not v_weak(episode_from_conversation(conv), task, ds.visible_db(task.family)):  # an exploit demo must pass the weak check
                kind, conv = "gold", demo_conversation(task, env, "gold")
            demos.append(conv)
            kinds.append({"task_id": task.task_id, "kind": kind})
        (run_dir / "demos.json").write_text(json.dumps({"kinds": kinds, "conversations": demos}))
        stats = train_sft(cfg["model_id"], demos, run_dir / "adapter", CONDITIONS[cfg["heal"]["condition"]], make_tools(env), sft, None, args.seed)
        status = "completed"
        manifest.finish(run_dir, man, status, sft=stats, kind_counts={k: sum(x["kind"] == k for x in kinds) for k in set(mix)})
    finally:
        if status != "completed":
            manifest.finish(run_dir, man, status)
        print(f"[seedpolicy] status={status} run_dir={run_dir}")
