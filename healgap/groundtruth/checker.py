"""G: ground truth. EVAL ONLY (hard rule 1): import this from healgap/eval/ and nowhere else.

The submitted SQL must return the gold result on all K ground-truth variants.
"""

from __future__ import annotations

from pathlib import Path

from healgap.env.dataset import Episode, Task, load_manifest
from healgap.verifiers.iso import matches_gold_on


def gt_dbs(profile: str, family: str, root: Path = Path("data")) -> list[Path]:
    return [root / "hidden" / profile / f"{family}_{s}.db" for s in load_manifest(profile, root)["gt_seeds"]]


def g(episode: Episode, task: Task, dbs: list[Path]) -> int:
    return int(matches_gold_on(episode.submitted_sql, task, dbs))
