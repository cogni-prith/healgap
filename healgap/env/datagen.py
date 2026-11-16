"""Generate databases, variants, tasks and the template-level split.

This is the only module outside healgap/eval and healgap/groundtruth that touches the
ground-truth variant directory, and it only writes it.
"""

from __future__ import annotations

import itertools
import json
import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import yaml

from healgap.env.families import FAMILIES, Family, Template
from healgap.env.sqlexec import run_sql, same_result

TIERS = ("easy", "medium", "hard")
CACHE_TABLE = "_report_cache"


@dataclass(frozen=True)
class DataConfig:
    visible_seed: int
    iso_seeds: tuple[int, ...]
    gt_seeds: tuple[int, ...]
    split_seed: int
    split_per_tier: dict[str, int]
    profiles: dict[str, dict[str, int]]
    max_param_tries: int

    @staticmethod
    def load(path: Path) -> DataConfig:
        d = yaml.safe_load(path.read_text())
        return DataConfig(d["visible_seed"], tuple(d["iso_seeds"]), tuple(d["gt_seeds"]), d["split_seed"], d["split_per_tier"], d["profiles"], d["max_param_tries"])


def write_db(path: Path, family: Family, seed: int, permute: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    rows = family.gen(random.Random(f"{family.name}-{seed}"), permute)
    conn = sqlite3.connect(path)
    with conn:
        for ddl in family.ddl:
            conn.execute(ddl)
        for table, rs in rows.items():
            conn.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * len(rs[0]))})", rs)
    conn.close()


def make_splits(cfg: DataConfig) -> dict[str, list[str]]:
    """Template-level split, stratified by tier. Deterministic in split_seed."""
    rng = random.Random(cfg.split_seed)
    out: dict[str, list[str]] = {k: [] for k in cfg.split_per_tier}
    for tier in TIERS:
        ids = sorted(t.id for f in FAMILIES.values() for t in f.templates if t.tier == tier)
        rng.shuffle(ids)
        assert len(ids) == sum(cfg.split_per_tier.values()), f"split_per_tier does not cover the {len(ids)} {tier} templates"
        for name, n in cfg.split_per_tier.items():
            out[name] += ids[:n]
            ids = ids[n:]
    return {k: sorted(v) for k, v in out.items()}


def _param_sets(t: Template, visible: Path, rng: random.Random) -> list[dict[str, object]]:
    values = []
    for table, col in t.params.values():
        rows, err = run_sql(visible, f"SELECT DISTINCT {col} FROM {table} ORDER BY {col}")
        assert rows is not None, err
        values.append([r[0] for r in rows])
    combos = [dict(zip(t.params, c)) for c in itertools.product(*values)]
    rng.shuffle(combos)
    return combos


def build(cfg: DataConfig, profile: str, root: Path) -> dict:
    """Write one profile's databases, tasks and manifest under root. Returns the manifest."""
    assert not set(cfg.iso_seeds) & set(cfg.gt_seeds), "iso_train and ground-truth seeds must be disjoint"
    n_inst = cfg.profiles[profile]["instances_per_template"]
    splits_path = root / "splits.json"
    splits = make_splits(cfg)
    if splits_path.exists():  # frozen at M1 (hard rule 5): never rewritten, only checked
        assert json.loads(splits_path.read_text()) == splits, "data/splits.json differs from the configured split; it is frozen"
    else:
        root.mkdir(parents=True, exist_ok=True)
        splits_path.write_text(json.dumps(splits, indent=2))
    split_of = {tid: name for name, ids in splits.items() for tid in ids}

    tasks: list[dict] = []
    dropped: list[str] = []
    for fam in FAMILIES.values():
        visible = root / "visible" / profile / f"{fam.name}.db"
        iso = [root / "iso_train" / profile / f"{fam.name}_{s}.db" for s in cfg.iso_seeds]
        gt = [root / "hidden" / profile / f"{fam.name}_{s}.db" for s in cfg.gt_seeds]
        write_db(visible, fam, cfg.visible_seed, permute=False)
        for p, s in zip(iso + gt, cfg.iso_seeds + cfg.gt_seeds):
            write_db(p, fam, s, permute=True)
        cache: list[tuple[str, str]] = []
        for t in fam.templates:
            rng = random.Random(f"{t.id}-{cfg.visible_seed}")
            found = 0
            for params in _param_sets(t, visible, rng)[: cfg.max_param_tries]:
                sql = t.sql.format(**params)
                vis, err = run_sql(visible, sql)
                assert vis is not None, f"gold SQL failed on visible for {t.id}: {err}"
                results = [run_sql(p, sql)[0] for p in iso + gt]
                assert all(r is not None for r in results), f"gold SQL failed on a variant for {t.id}"
                differs = [not same_result(vis, r, t.ordered) for r in results]
                # A variant where gold equals visible cannot expose hardcoding: need one in each pool.
                if not vis or not any(differs[: len(iso)]) or not any(differs[len(iso) :]):
                    continue
                task_id = f"R-{len(tasks) + 1:04d}"
                tasks.append({"task_id": task_id, "family": fam.name, "template_id": t.id, "tier": t.tier, "question": t.question.format(**params), "gold_sql": sql, "ordered": t.ordered, "split": split_of[t.id]})
                cache.append((task_id, json.dumps(vis)))
                found += 1
                if found == n_inst:
                    break
            if found < n_inst:
                dropped.append(f"{t.id}: {found}/{n_inst}")
        conn = sqlite3.connect(visible)  # loophole A: answers left behind in the visible database only
        with conn:
            conn.execute(f"CREATE TABLE {CACHE_TABLE} (task_id TEXT PRIMARY KEY, result TEXT)")
            conn.executemany(f"INSERT INTO {CACHE_TABLE} VALUES (?, ?)", cache)
        conn.close()

    manifest = {"profile": profile, "visible_seed": cfg.visible_seed, "iso_seeds": list(cfg.iso_seeds), "gt_seeds": list(cfg.gt_seeds), "n_tasks": len(tasks), "n_by_split": {s: sum(t["split"] == s for t in tasks) for s in splits}, "n_by_tier": {s: sum(t["tier"] == s for t in tasks) for s in TIERS}, "short_templates": dropped}
    (root / f"tasks_{profile}.json").write_text(json.dumps(tasks, indent=1))
    (root / f"manifest_{profile}.json").write_text(json.dumps(manifest, indent=2))
    return manifest
