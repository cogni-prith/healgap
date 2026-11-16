"""Run manifest (hard rule 6): git commit, full config, seed, model id, library versions, start and end time."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
_LIBS = ("agenttune", "trl", "transformers", "torch", "peft", "datasets", "accelerate")


def _git_commit() -> str | None:
    r = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else None


def start(run_dir: Path, config: dict[str, Any], seed: int, model_id: str, label: str) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    m = {
        "run_id": run_dir.name,
        "label": label,
        "git_commit": _git_commit(),
        "config": config,
        "seed": seed,
        "model_id": model_id,
        "versions": {p: version(p) for p in _LIBS},
        "python": sys.version,
        "platform": platform.platform(),
        "start_time": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": "running",
    }
    (run_dir / "manifest.json").write_text(json.dumps(m, indent=2))
    return m


def finish(run_dir: Path, manifest: dict[str, Any], status: str, **extra: Any) -> None:
    manifest.update(status=status, end_time=time.strftime("%Y-%m-%dT%H:%M:%S%z"), **extra)
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=repr))
