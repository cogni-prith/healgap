"""R_iso: isomorphic reward. The submitted SQL must match gold on the visible database and
on m resampled variants from the iso_train pool. Full content comparison on every tier."""

from __future__ import annotations

import random
from pathlib import Path

from healgap.env.dataset import Episode, Task
from healgap.env.sqlexec import run_sql, same_result


def matches_gold_on(sql: str | None, task: Task, dbs: list[Path]) -> bool:
    """True if sql returns the gold result on every database in dbs."""
    if sql is None:
        return False
    return all(same_result(run_sql(db, sql)[0], run_sql(db, task.gold_sql)[0], task.ordered) for db in dbs)


def sample_variants(pool: list[Path], m: int, rng: random.Random) -> list[Path]:
    return rng.sample(pool, m)


def r_iso(episode: Episode, task: Task, visible_db: Path, variants: list[Path]) -> int:
    return int(matches_gold_on(episode.submitted_sql, task, [visible_db, *variants]))
