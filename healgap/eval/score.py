"""Turn collected rollout rows into metric records (W, G, label, ...). Eval side: uses ground truth."""

from __future__ import annotations

from collections.abc import Callable

from healgap.env.dataset import Dataset, Episode
from healgap.groundtruth.checker import g, gt_dbs
from healgap.groundtruth.labeller import label
from healgap.verifiers.weak import v_weak


def score_rows(rows: list[dict], ds: Dataset, seed: int, flag: Callable[[Episode], int] | None = None) -> list[dict]:
    """One record per row, in the shape healgap.eval.metrics expects. flag is the detector (F = 0 if None)."""
    out = []
    for row in rows:
        ep: Episode = row["episode"]
        task = ds.tasks[ep.task_id]
        vis, gts = ds.visible_db(task.family), gt_dbs(ds.profile, task.family, ds.root)
        out.append({
            "task_id": task.task_id,
            "seed": seed,
            "tier": task.tier,
            "W": v_weak(ep, task, vis),
            "G": g(ep, task, gts),
            "F": int(flag(ep)) if flag else 0,
            "label": label(ep, task, vis, gts),
            "submitted": ep.submitted_sql is not None,
            "steps": row["steps"],
            "tool_calls": row["tool_calls"],
            "tool_errors": row["tool_errors"],
        })
    return out
