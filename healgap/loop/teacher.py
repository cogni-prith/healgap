"""Scripted teacher: the corrective trajectory for a failed episode, and trimming of kept trajectories.

The teacher explores the schema, runs the gold query, then submits it. Tool outputs come from the real tools
on the visible database, so corrective data looks like a real rollout.
"""

from __future__ import annotations

import json

from healgap.env.dataset import Task
from healgap.env.prompts import user_prompt
from healgap.env.tools import SAVED, SqlEnv, make_tools

FINAL_TEXT = "The report has been submitted."


def _turn(name: str, args: dict, output: str) -> list[dict]:
    call = {"type": "function", "function": {"name": name, "arguments": json.dumps(args)}}
    return [{"role": "assistant", "content": "", "tool_calls": [call]}, {"role": "tool", "name": name, "content": output}]


def teacher_conversation(task: Task, env: SqlEnv) -> list[dict]:
    list_tables, _describe, run_query, submit = make_tools(env)
    conv = user_prompt(task)
    env.pre_step_hook(0, conv)
    conv += _turn("list_tables", {}, list_tables())
    env.pre_step_hook(1, conv)
    conv += _turn("run_query", {"sql": task.gold_sql}, run_query(task.gold_sql))
    env.pre_step_hook(2, conv)
    conv += _turn("submit", {"sql": task.gold_sql}, submit(task.gold_sql))
    return conv + [{"role": "assistant", "content": FINAL_TEXT}]


def trim_kept(conversation: list[dict]) -> list[dict]:
    """A kept policy trajectory, without the system message, cut after the accepted submit."""
    out: list[dict] = []
    for m in conversation:
        if m.get("role") == "system":
            continue
        out.append(m)
        if m.get("role") == "tool" and SAVED in str(m.get("content", "")):
            break
    # Drop calls the model made after its accepted submit in the same turn: their results were cut above.
    last = max(i for i, m in enumerate(out) if m.get("role") == "assistant")
    calls = out[last].get("tool_calls") or []
    names = [c.get("function", c).get("name") for c in calls]
    if "submit" in names:
        out[last] = {**out[last], "tool_calls": calls[: names.index("submit") + 1]}
        out = out[: last + 1 + names.index("submit") + 1]
    return out + [{"role": "assistant", "content": FINAL_TEXT}]
