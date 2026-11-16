"""Heal loop: collect, detect, classify, generate corrective data, retrain, gate. Resumable per round.

This is our own loop around AgentTune's trainers (docs/DECISIONS.md, M0 question 2).
Ground truth never enters here: the detector arrives as an opaque flag function and evaluation is a callback.
"""

from __future__ import annotations

import gc
import json
import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from healgap.env.dataset import Dataset, Episode, Task, load_dataset
from healgap.env.prompts import CONDITIONS
from healgap.env.tools import SqlEnv, episode_from_conversation, episode_stats, make_tools
from healgap.loop.rollout import GenConfig, collect, make_rollout_fn
from healgap.loop.teacher import teacher_conversation, trim_kept
from healgap.train.sft import SftConfig, train_sft
from healgap.verifiers.iso import r_iso, sample_variants
from healgap.verifiers.weak import v_weak


@dataclass(frozen=True)
class ArmConfig:
    name: str
    signal: str  # weak | iso : which verifier decides that a trajectory is kept as a positive
    detector: str  # none | rule | sim | oracle
    iso_from_round: int | None = None  # switch the signal to iso from this round on (the repair arm)
    sim_recall: float | None = None
    sim_fpr: float | None = None


@dataclass(frozen=True)
class HealConfig:
    label: str
    profile: str
    model_id: str
    condition: str
    gen: GenConfig
    sft: SftConfig
    rounds: int
    collect_per_round: int
    gate_tasks: int
    eval_samples: int
    iso_m: int
    start_adapter: str | None  # path template with {seed}: the seeded starting policy. None starts from the base model.
    arm: ArmConfig

    @staticmethod
    def from_dict(d: dict[str, Any]) -> HealConfig:
        h = d["heal"]
        sft = SftConfig(**{**d["sft"], "lora_targets": tuple(d["sft"]["lora_targets"])})
        return HealConfig(d["label"], d["profile"], d["model_id"], h["condition"], GenConfig(**d["gen"]), sft, h["rounds"], h["collect_per_round"], h["gate_tasks"], h["eval_samples"], h["iso_m"], h.get("start_adapter"), ArmConfig(**d["arm"]))


def _rows_to_json(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in r.items() if k != "episode"} for r in rows]


def _rows_from_json(rows: list[dict]) -> list[dict]:
    return [{**r, "episode": episode_from_conversation(r["conversation"])} for r in rows]


class Policy:
    """Base model plus an optional LoRA adapter, loaded for rollouts and freed afterwards."""

    def __init__(self, model_id: str, adapter: Path | None) -> None:
        self.tok = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.bfloat16).to("cuda")
        self.model = (PeftModel.from_pretrained(model, str(adapter)) if adapter else model).eval()

    def free(self) -> None:
        del self.model
        gc.collect()
        torch.cuda.empty_cache()


def classify(ep: Episode, w: int, flagged: int) -> str:
    """Failure type from detector output and simple rules."""
    if flagged:
        return "cheat_flagged"
    if w:
        return "pass"
    if ep.submitted_sql is None:
        return "no_submit"
    return "sql_error" if any(c.name == "run_query" and c.output.startswith("Error") for c in ep.tool_calls[-2:]) else "wrong_result"


def run_heal(cfg: HealConfig, seed: int, run_dir: Path, flag: Callable[[Episode], int], evaluate: Callable[[str, list[dict]], None], cache_dir: Path, root: Path = Path("data")) -> None:
    ds: Dataset = load_dataset(cfg.profile, root)
    env = SqlEnv(ds, cfg.gen.max_rows, cfg.gen.timeout_s)
    system_prompt = CONDITIONS[cfg.condition]
    rng = random.Random(seed)
    train = sorted(ds.split("train"), key=lambda t: t.task_id)
    rng.shuffle(train)
    assert cfg.rounds * cfg.collect_per_round <= len(train), "not enough train tasks for the configured rounds"
    batches = [train[i * cfg.collect_per_round : (i + 1) * cfg.collect_per_round] for i in range(cfg.rounds)]
    gate_tasks = sorted(ds.split("gate"), key=lambda t: t.task_id)[: cfg.gate_tasks]
    eval_tasks = sorted(ds.split("eval"), key=lambda t: t.task_id)

    def signal_at(round_no: int) -> str:
        return "iso" if cfg.arm.signal == "iso" or (cfg.arm.iso_from_round is not None and round_no >= cfg.arm.iso_from_round) else "weak"

    def passes(ep: Episode, task: Task, signal: str) -> int:
        vis = ds.visible_db(task.family)
        if signal == "iso":
            return r_iso(ep, task, vis, sample_variants(ds.iso_dbs(task.family), cfg.iso_m, rng))
        return v_weak(ep, task, vis)

    def rollouts(policy: Policy | None, adapter: Path | None, tasks: list[Task], n: int, purpose: str, torch_seed: int) -> list[dict]:
        """Rollouts of the starting policy are the same for every arm at a given seed, so they are cached on disk."""
        cache = cache_dir / f"{cfg.model_id.replace('/', '_')}_{cfg.profile}_{cfg.condition}_{'seeded' if start else 'base'}_seed{seed}_{purpose}.json" if adapter == start else None
        if cache is not None and cache.exists():
            return _rows_from_json(json.loads(cache.read_text()))
        own = policy is None
        policy = policy or Policy(cfg.model_id, adapter)
        torch.manual_seed(torch_seed)
        rows = collect(make_rollout_fn(env, system_prompt, cfg.gen, policy.model, policy.tok), tasks, n, cfg.gen)
        if own:
            policy.free()
        if cache is not None:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(_rows_to_json(rows), default=str))
        return rows

    def gate_stats(rows: list[dict], signal: str) -> dict[str, float]:
        eps = [r["episode"] for r in rows]
        return {"signal_success": sum(passes(e, ds.tasks[e.task_id], signal) for e in eps) / len(eps), "flag_rate": sum(flag(e) for e in eps) / len(eps), "n": len(eps)}

    start: Path | None = Path(cfg.start_adapter.format(seed=seed)) if cfg.start_adapter else None
    assert start is None or (start / "adapter_config.json").exists(), f"starting adapter not found: {start}"
    deployed: Path | None = start
    deployed_name = "start"
    state_path = run_dir / "state.json"
    done: list[dict] = json.loads(state_path.read_text()) if state_path.exists() else []
    if done:
        deployed = Path(done[-1]["deployed_adapter"]) if done[-1]["deployed_adapter"] else None
        deployed_name = done[-1]["deployed"]
    else:
        evaluate("round0_start", rollouts(None, start, eval_tasks, cfg.eval_samples, "eval", seed))

    for round_no in range(len(done) + 1, cfg.rounds + 1):
        rdir = run_dir / f"round{round_no}"
        rdir.mkdir(parents=True, exist_ok=True)
        signal = signal_at(round_no)
        use_detector = signal == "weak"

        # 1-3. collect with the deployed policy, detect, classify
        dep = Policy(cfg.model_id, deployed) if deployed != start else None  # the starting policy's rollouts come from the cache
        rows = rollouts(dep, deployed, batches[round_no - 1], 1, f"collect_r{round_no}", seed * 1000 + round_no)
        dep_gate_rows = rollouts(dep, deployed, gate_tasks, 1, "gate", seed * 1000 + 500 + round_no)
        if dep is not None:
            dep.free()
        curated, log = [], []
        for row in rows:
            ep: Episode = row["episode"]
            task = ds.tasks[ep.task_id]
            flagged = flag(ep) if use_detector else 0
            ok = passes(ep, task, signal)
            kept = bool(ok and not flagged)
            # 4. corrective data: scripted teacher trajectory for every failure, own trajectory for every kept pass
            curated.append(trim_kept(row["conversation"]) if kept else teacher_conversation(task, env))
            log.append({"task_id": ep.task_id, "signal_pass": ok, "flagged": flagged, "kept": kept, "failure_type": classify(ep, ok, flagged), "submitted_sql": ep.submitted_sql, **episode_stats(row["conversation"], ep)})
        (rdir / "collect.jsonl").write_text("\n".join(json.dumps(x) for x in log))
        (rdir / "curated.json").write_text(json.dumps(curated, default=str))

        # 5. retrain: corrective SFT continuing from the deployed adapter
        adapter = rdir / "adapter"
        sft_stats = train_sft(cfg.model_id, curated, adapter, system_prompt, make_tools(env), cfg.sft, deployed, seed)

        # 6. gate, then 7. evaluate the candidate (evaluation is outside the loop)
        cand = Policy(cfg.model_id, adapter)
        cand_gate = gate_stats(rollouts(cand, adapter, gate_tasks, 1, "gate", seed * 1000 + 600 + round_no), signal)
        dep_gate = gate_stats(dep_gate_rows, signal)
        deploy = cand_gate["signal_success"] >= dep_gate["signal_success"] and (not use_detector or cand_gate["flag_rate"] <= dep_gate["flag_rate"])
        evaluate(f"round{round_no}_candidate", rollouts(cand, adapter, eval_tasks, cfg.eval_samples, "eval", seed))
        cand.free()

        parent = deployed
        if deploy:
            deployed, deployed_name = adapter, f"round{round_no}_candidate"
        done.append({
            "round": round_no,
            "signal": signal,
            "detector_used": cfg.arm.detector if use_detector else "none",
            "n_collected": len(log),
            "n_kept": sum(x["kept"] for x in log),
            "n_flagged": sum(x["flagged"] for x in log),
            "failure_types": {t: sum(x["failure_type"] == t for x in log) for t in ("pass", "cheat_flagged", "no_submit", "sql_error", "wrong_result")},
            "sft": sft_stats,
            "parent_adapter": str(parent) if parent else None,
            "candidate_gate": cand_gate,
            "deployed_gate": dep_gate,
            "gate_decision": "deploy" if deploy else "reject",
            "deployed": deployed_name,
            "deployed_adapter": str(deployed) if deployed else None,
        })
        state_path.write_text(json.dumps(done, indent=2))
