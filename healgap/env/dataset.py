"""Task and episode types, and loading of the agent-visible side of a generated dataset.

Nothing here opens the ground-truth variant pool. The manifest lists that pool's seeds
(numbers only) so that variant pool separation can be asserted at load time (hard rule 2).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Task:
    task_id: str
    family: str
    template_id: str
    tier: str
    question: str
    gold_sql: str
    ordered: bool
    split: str


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict
    output: str = ""


@dataclass(frozen=True)
class Episode:
    """One agent run. submitted_sql is the SQL of the first submit call, or None."""

    task_id: str
    tool_calls: tuple[ToolCall, ...]
    submitted_sql: str | None


@dataclass(frozen=True)
class Dataset:
    profile: str
    root: Path
    tasks: dict[str, Task]
    iso_seeds: tuple[int, ...]

    def visible_db(self, family: str) -> Path:
        return self.root / "visible" / self.profile / f"{family}.db"

    def iso_dbs(self, family: str) -> list[Path]:
        return [self.root / "iso_train" / self.profile / f"{family}_{s}.db" for s in self.iso_seeds]

    def split(self, name: str) -> list[Task]:
        return [t for t in self.tasks.values() if t.split == name]


def load_manifest(profile: str, root: Path) -> dict:
    return json.loads((root / f"manifest_{profile}.json").read_text())


def load_dataset(profile: str, root: Path = Path("data")) -> Dataset:
    m = load_manifest(profile, root)
    overlap = set(m["iso_seeds"]) & set(m["gt_seeds"]) | {m["visible_seed"]} & (set(m["iso_seeds"]) | set(m["gt_seeds"]))
    assert not overlap, f"variant pools share seeds: {sorted(overlap)}"
    tasks = {d["task_id"]: Task(**d) for d in json.loads((root / f"tasks_{profile}.json").read_text())}
    return Dataset(profile, root, tasks, tuple(m["iso_seeds"]))
