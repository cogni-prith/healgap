"""Rollouts through AgentTune's rollout engine, outside a trainer (collection and evaluation).

The same create_rollout_fn is what GRPO training uses, so collection, evaluation and training share the tool
loop, the tool-call parser and the prompt format.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agenttune.agentic.rollout_engines.rollout_factory import create_rollout_fn

from healgap.env.dataset import Task
from healgap.env.prompts import user_prompt
from healgap.env.tools import SqlEnv, episode_from_conversation, episode_stats, make_tools


@dataclass(frozen=True)
class GenConfig:
    max_new_tokens: int
    temperature: float
    max_tool_rounds: int
    max_rows: int
    timeout_s: float


def make_rollout_fn(env: SqlEnv, system_prompt: str, gen: GenConfig, model: Any = None, tokenizer: Any = None) -> Callable:
    """With model and tokenizer: a standalone rollout function. Without: one to pass to a trainer as rollout_func."""
    return create_rollout_fn(
        rollout_backend="transformers" if model is not None else None,
        model=model,
        tokenizer=tokenizer,
        tools=make_tools(env),
        max_steps=gen.max_tool_rounds,
        system_prompt=system_prompt,
        pre_step_hook=env.pre_step_hook,
    )


def collect(rollout_fn: Callable, tasks: list[Task], n_samples: int, gen: GenConfig) -> list[dict]:
    """n_samples sampled episodes per task. One row per episode: task id, conversation, episode, stats, seconds."""
    rows = []
    for task in tasks:
        for k in range(n_samples):
            t0 = time.time()
            out = rollout_fn([user_prompt(task)], max_new_tokens=gen.max_new_tokens, temperature=gen.temperature, do_sample=True)
            conv = out["conversations"][0]
            ep = episode_from_conversation(conv)
            assert ep.task_id == task.task_id
            rows.append({"task_id": task.task_id, "sample": k, "conversation": conv, "episode": ep, "seconds": time.time() - t0, **episode_stats(conv, ep)})
    return rows
