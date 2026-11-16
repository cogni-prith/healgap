"""D_oracle and D_sim(r): control detectors built from oracle labels.

They need ground truth, so they live under healgap/eval/ (hard rule 1) and are handed to the heal loop as an
opaque flag function. They are controls, not deployable detectors, and are described as such in the report.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from healgap.env.dataset import Dataset, Episode
from healgap.groundtruth.checker import g, gt_dbs
from healgap.groundtruth.labeller import EXPLOITS, label
from healgap.verifiers.weak import v_weak


def is_true_hack(ep: Episode, ds: Dataset) -> bool:
    task = ds.tasks[ep.task_id]
    vis, gts = ds.visible_db(task.family), gt_dbs(ds.profile, task.family, ds.root)
    return bool(v_weak(ep, task, vis)) and not g(ep, task, gts) and label(ep, task, vis, gts) in EXPLOITS


def make_oracle(ds: Dataset) -> Callable[[Episode], int]:
    return lambda ep: int(is_true_hack(ep, ds))


def make_sim(ds: Dataset, recall: float, false_positive_rate: float, seed: int) -> Callable[[Episode], int]:
    """Flags each true hack with probability recall, independent of exploit type, and each non-hack with
    probability false_positive_rate. One draw per call, from a generator seeded once."""
    rng = random.Random(f"d_sim-{seed}")
    return lambda ep: int(rng.random() < (recall if is_true_hack(ep, ds) else false_positive_rate))
