"""Read-only SQL execution on a SQLite file, and result comparison."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

Result = list[tuple]


def run_sql(db: Path, sql: str, max_rows: int | None = None, timeout_s: float = 2.0) -> tuple[Result | None, str | None]:
    """Run one statement read-only. Returns (rows, None) or (None, error message).

    ATTACH is denied so a query cannot reach another database file.
    """
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        deadline = time.monotonic() + timeout_s
        conn.set_progress_handler(lambda: time.monotonic() > deadline, 10_000)
        conn.set_authorizer(lambda action, *_: sqlite3.SQLITE_DENY if action in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH) else sqlite3.SQLITE_OK)
        cur = conn.execute(sql)
        rows = cur.fetchmany(max_rows) if max_rows is not None else cur.fetchall()
        return [tuple(r) for r in rows], None
    except (sqlite3.Error, sqlite3.Warning, ValueError) as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        conn.close()


def _norm(v: object) -> object:
    return round(float(v), 6) if isinstance(v, (int, float)) and not isinstance(v, bool) else v


def same_result(a: Result | None, b: Result | None, ordered: bool) -> bool:
    """Equal row multisets (or sequences if ordered). 5 and 5.0 compare equal."""
    if a is None or b is None:
        return False
    na = [tuple(_norm(v) for v in r) for r in a]
    nb = [tuple(_norm(v) for v in r) for r in b]
    return na == nb if ordered else sorted(na, key=repr) == sorted(nb, key=repr)


def same_shape(a: Result | None, b: Result | None) -> bool:
    """Same row count and same column count."""
    if a is None or b is None or len(a) != len(b):
        return False
    return not a or len(a[0]) == len(b[0])
