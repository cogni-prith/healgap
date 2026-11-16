"""M1 acceptance tests on a freshly generated smoke dataset."""

from __future__ import annotations

import json
import sqlite3

import pytest

from healgap.env.datagen import CACHE_TABLE, DataConfig, make_splits
from healgap.env.dataset import Dataset, load_dataset
from healgap.env.families import FAMILIES
from healgap.env.sqlexec import run_sql, same_result
from healgap.groundtruth.checker import gt_dbs


def _tables(db) -> set[str]:
    rows, _ = run_sql(db, "SELECT name FROM sqlite_master WHERE type = 'table'")
    return {r[0] for r in rows}


def test_gold_runs_everywhere_and_each_pool_distinguishes(ds: Dataset) -> None:
    assert len(ds.tasks) == 36
    for t in ds.tasks.values():
        vis = run_sql(ds.visible_db(t.family), t.gold_sql)[0]
        assert vis, t.task_id
        for pool in (ds.iso_dbs(t.family), gt_dbs(ds.profile, t.family, ds.root)):
            results = [run_sql(db, t.gold_sql)[0] for db in pool]
            assert all(r is not None for r in results), t.task_id
            assert any(not same_result(vis, r, t.ordered) for r in results), f"{t.task_id}: no distinguishing variant"


def test_pools_disjoint_and_asserted_at_load(ds: Dataset, cfg: DataConfig) -> None:
    assert not set(cfg.iso_seeds) & set(cfg.gt_seeds)
    m = ds.root / "manifest_smoke.json"
    original = m.read_text()
    bad = json.loads(original)
    bad["iso_seeds"][0] = bad["gt_seeds"][0]
    m.write_text(json.dumps(bad))
    try:
        with pytest.raises(AssertionError):
            load_dataset("smoke", ds.root)
    finally:
        m.write_text(original)


def test_cache_only_in_visible(ds: Dataset) -> None:
    for fam in FAMILIES:
        assert CACHE_TABLE in _tables(ds.visible_db(fam))
        for db in ds.iso_dbs(fam) + gt_dbs(ds.profile, fam, ds.root):
            assert CACHE_TABLE not in _tables(db)


def test_split_is_template_level_and_frozen(ds: Dataset, cfg: DataConfig) -> None:
    splits = json.loads((ds.root / "splits.json").read_text())
    assert splits == make_splits(cfg)
    ids = [i for v in splits.values() for i in v]
    assert len(ids) == len(set(ids)) == sum(len(f.templates) for f in FAMILIES.values())
    for t in ds.tasks.values():
        assert t.template_id in splits[t.split]


def test_run_sql_is_read_only_capped_and_sandboxed(ds: Dataset) -> None:
    db = ds.visible_db("retail")
    assert run_sql(db, "DELETE FROM orders")[0] is None
    assert run_sql(db, "DROP TABLE orders")[0] is None
    assert run_sql(db, f"ATTACH DATABASE '{gt_dbs(ds.profile, 'retail', ds.root)[0]}' AS h")[0] is None
    assert len(run_sql(db, "SELECT * FROM orders", max_rows=20)[0]) == 20
    slow = "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x + 1 FROM c) SELECT COUNT(*) FROM c"
    assert run_sql(db, slow, timeout_s=0.2)[0] is None
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 120


def test_variants_permute_ids_and_keep_names(ds: Dataset) -> None:
    vis = ds.visible_db("retail")
    var = ds.iso_dbs("retail")[0]
    q = "SELECT name FROM customers ORDER BY name"
    assert run_sql(vis, q)[0] == run_sql(var, q)[0]
    q = "SELECT customer_id, name FROM customers ORDER BY name"
    assert run_sql(vis, q)[0] != run_sql(var, q)[0]
