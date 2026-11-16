"""Evaluation callback for the heal loop. Scores a policy's eval rollouts with ground truth and writes them.

Each record carries F (the arm's detector) and F_rule (D_rule), so reported hack rate is comparable across arms.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

from healgap.detectors.rule import d_rule
from healgap.env.dataset import Dataset, Episode
from healgap.eval.score import score_rows


def make_evaluator(ds: Dataset, run_dir: Path, seed: int, flag: Callable[[Episode], int]) -> Callable[[str, list[dict]], None]:
    out_dir = run_dir / "eval"
    out_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(name: str, rows: list[dict]) -> None:
        records = score_rows(rows, ds, seed, flag)
        with (out_dir / f"{name}.jsonl").open("w") as f:
            for row, rec in zip(rows, records):
                ep: Episode = row["episode"]
                f.write(json.dumps({**rec, "F_rule": d_rule(ep), "policy": name, "sample": row["sample"], "seconds": row["seconds"], "submitted_sql": ep.submitted_sql, "conversation": row["conversation"]}, default=str) + "\n")

    return evaluate
