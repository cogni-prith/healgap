"""M0 GRPO smoke: SmolLM2-360M, one trivial tool, one custom reward.

SMOKE RUN. Proves the AgentTune training path runs end to end and records what a
custom reward function actually receives (M0 question 1). Not a result.

Usage: python scripts/m0_grpo_smoke.py --seed 0 --max-steps 6
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from datasets import Dataset

from agenttune.core.backend_factory import create_agentic_trainer

MODEL_ID = "HuggingFaceTB/SmolLM2-360M-Instruct"
ROOT = Path(__file__).resolve().parents[1]


def git_commit() -> str | None:
    r = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--max-steps", type=int, default=6)
    ap.add_argument("--batch-size", type=int, default=4, help="num_generations stays 4; 8 gives 2 distinct prompts per reward call")
    args = ap.parse_args()

    run_id = f"m0_grpo_smoke_seed{args.seed}_{time.strftime('%Y%m%dT%H%M%S')}"
    run_dir = ROOT / "runs" / run_id
    run_dir.mkdir(parents=True)
    tool_log = run_dir / "tool_calls.jsonl"
    reward_log = run_dir / "reward_calls.jsonl"

    def add(a: int, b: int) -> int:
        """
        Add two integers.

        Args:
            a: The first integer.
            b: The second integer.

        Returns:
            The sum of a and b.
        """
        with tool_log.open("a") as f:
            f.write(json.dumps({"a": repr(a), "b": repr(b), "t": time.time()}) + "\n")
        return int(a) + int(b)

    def probe_reward(prompts: Any = None, completions: Any = None, answer: Any = None, **kwargs: Any) -> list[float]:
        """1.0 if the gold answer string appears anywhere in the completion, else 0.0.

        Also dumps the types and one raw sample of everything it was given.
        """
        n = len(completions)
        answers = answer if isinstance(answer, list) else [answer] * n
        rewards = [1.0 if str(g) in json.dumps(c, default=str) else 0.0 for c, g in zip(completions, answers, strict=True)]
        record = {
            "n_completions": n,
            "type_prompts": type(prompts).__name__,
            "type_completion0": type(completions[0]).__name__,
            "completion0": completions[0],
            "prompt0": prompts[0] if prompts else None,
            "answer": answers,
            "kwargs_keys": sorted(kwargs),
            "kwargs_types": {k: type(v).__name__ for k, v in kwargs.items()},
            "kwargs_lens": {k: len(v) for k, v in kwargs.items() if hasattr(v, "__len__")},
            "kwargs_sample0": {k: (v[0] if isinstance(v, list) and v else v) for k, v in kwargs.items()},
            "rewards": rewards,
            # alignment probe: for every index, the dataset columns and the user turn the rollout actually saw
            "all_task_id": kwargs.get("task_id"),
            "all_db_path": kwargs.get("db_path"),
            "all_prompt_user": [p[-1]["content"] for p in prompts] if prompts else None,
            "all_conversation_user": [
                next((m["content"] for m in conv if m.get("role") == "user"), None)
                for conv in kwargs.get("conversations", [])
            ],
        }
        with reward_log.open("a") as f:
            f.write(json.dumps(record, default=repr) + "\n")
        return rewards

    pairs = [(2, 3), (4, 5), (10, 7), (6, 6), (1, 8), (12, 30), (9, 9), (3, 14)]
    ds = Dataset.from_dict(
        {
            "prompt": [
                [{"role": "user", "content": f"Use the add tool to compute {a}+{b}, then state the result."}]
                for a, b in pairs
            ],
            "answer": [str(a + b) for a, b in pairs],
            "task_id": [f"task_{i:03d}" for i in range(len(pairs))],
            "db_path": [f"data/visible/fake_{i:03d}.db" for i in range(len(pairs))],
        }
    )

    config: dict[str, Any] = {
        "algorithm": "grpo",
        "backend": "trl",
        "model": MODEL_ID,
        "output_dir": str(run_dir / "adapter"),
        "max_steps": args.max_steps,
        "per_device_train_batch_size": args.batch_size,
        "gradient_accumulation_steps": 1,
        "learning_rate": 1e-5,
        "num_generations": 4,
        "max_completion_length": 128,
        "max_steps_per_turn": 3,
        "beta": 0.04,
        "seed": args.seed,
        "logging_steps": 1,
        "save_steps": 10000,
        "use_vllm": False,
        "log_completions": True,
        "report_to": "none",
        "peft_config": {"r": 8, "lora_alpha": 16, "task_type": "CAUSAL_LM", "target_modules": ["q_proj", "v_proj"]},
    }
    manifest: dict[str, Any] = {
        "run_id": run_id,
        "label": "smoke",
        "git_commit": git_commit(),
        "git_commit_note": "null means the repo had no commit when the run started",
        "config": config,
        "seed": args.seed,
        "model_id": MODEL_ID,
        "versions": {p: version(p) for p in ("agenttune", "trl", "transformers", "torch", "peft", "datasets", "accelerate")},
        "python": sys.version,
        "platform": platform.platform(),
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    status = "failed"
    try:
        trainer = create_agentic_trainer(train_dataset=ds, tools=[add], reward_funcs=probe_reward, **config)
        stats = trainer.train()
        manifest["train_stats"] = json.loads(json.dumps(stats, default=repr))
        manifest["log_history"] = json.loads(json.dumps(trainer.trainer.state.log_history, default=repr))
        status = "completed"
    finally:
        manifest["status"] = status
        manifest["end_time"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        manifest["n_tool_calls"] = sum(1 for _ in tool_log.open()) if tool_log.exists() else 0
        manifest["n_reward_calls"] = sum(1 for _ in reward_log.open()) if reward_log.exists() else 0
        manifest["adapter_files"] = sorted(p.name for p in (run_dir / "adapter").glob("*")) if (run_dir / "adapter").exists() else []
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
        print(f"[m0] status={status} run_dir={run_dir} tool_calls={manifest['n_tool_calls']} reward_calls={manifest['n_reward_calls']}")


if __name__ == "__main__":
    main()
