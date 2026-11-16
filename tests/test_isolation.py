"""Hard rule 1: ground truth is reachable only from healgap/eval/.

Fails if any module outside healgap/eval/ and healgap/groundtruth/ imports healgap.groundtruth, or mentions the
ground-truth data directory. healgap/env/datagen.py is the one exception: it writes that directory and never reads it.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ALLOWED_DIRS = (REPO / "healgap" / "eval", REPO / "healgap" / "groundtruth")
WRITER = REPO / "healgap" / "env" / "datagen.py"
EVAL_SCRIPTS = {"evaluate.py", "make_report.py", "exp0_base_rates.py"}


def _guarded_files() -> list[Path]:
    files = [p for p in (REPO / "healgap").rglob("*.py") if not any(d in p.parents for d in ALLOWED_DIRS)]
    files += [p for p in (REPO / "scripts").glob("*.py") if p.name not in EVAL_SCRIPTS]
    return files


def _imports(tree: ast.AST) -> list[str]:
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out += [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            out += [node.module] + [f"{node.module}.{a.name}" for a in node.names]
    return out


def test_no_ground_truth_import_outside_eval() -> None:
    files = _guarded_files()
    assert len(files) > 5
    for p in files:
        tree = ast.parse(p.read_text())
        bad = [m for m in _imports(tree) if "groundtruth" in m]
        assert not bad, f"{p.relative_to(REPO)} imports ground truth: {bad}"


def test_no_ground_truth_data_path_outside_eval() -> None:
    for p in _guarded_files():
        if p == WRITER:
            continue
        strings = [n.value for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        bad = [s for s in strings if "hidden" in s.lower() and len(s) < 200]
        assert not bad, f"{p.relative_to(REPO)} mentions the ground-truth directory: {bad}"


def test_eval_scripts_are_the_only_script_exception() -> None:
    for p in (REPO / "scripts").glob("*.py"):
        uses = any("groundtruth" in m for m in _imports(ast.parse(p.read_text())))
        assert not uses or p.name in EVAL_SCRIPTS, p.name
