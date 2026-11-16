"""AuditKIT pass over the starting policy and each arm's final deployed policy, pooled over seeds.

Usage: python scripts/auditkit_all.py --runs runs/ --label reduced --profile full
Runs scripts/auditkit_eval.py per run and writes runs/report_<label>/auditkit.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=Path("runs"))
    ap.add_argument("--label", default="reduced")
    ap.add_argument("--profile", default="full")
    args = ap.parse_args()
    groups: dict[str, list[Path]] = defaultdict(list)
    latest: dict[tuple, Path] = {}
    for d in sorted(args.runs.glob(f"heal_{args.label}_*")):
        man = json.loads((d / "manifest.json").read_text())
        if man.get("status") == "completed":
            latest[(man["config"]["arm"]["name"], man["seed"])] = d
    for (arm, seed), d in sorted(latest.items()):
        state = json.loads((d / "state.json").read_text())
        final = "round0_start" if state[-1]["deployed"] == "start" else state[-1]["deployed"]
        for name, group in ((final, f"{arm}: deployed after round {state[-1]['round']}"), ("round0_start", "starting policy (seeded)")):
            if group.startswith("starting") and arm != sorted({a for a, _ in latest})[0]:
                continue  # the starting policy's eval is the same file content in every arm: count it once per seed
            out = d / "auditkit" / name
            subprocess.run([sys.executable, "scripts/auditkit_eval.py", "--episodes", str(d / "eval" / f"{name}.jsonl"), "--profile", args.profile, "--out", str(out)], check=True, capture_output=True)
            groups[group].append(out.with_suffix(".json"))
    md = ["## AuditKIT (offline, no judge model)", "", "Per-episode AuditKIT diagnostics averaged over episodes, pooled over seeds. Verified success is AuditKIT's outcome verdict from our ground truth G passed as a CustomPredicate. Tool-call F1 by name is against the scripted teacher's route (list_tables, run_query, submit).", "", "| policy | episodes | verified success | tool-call validity | tool-call F1 (name) | redundant calls (lower is better) | loop-free |", "|---|---|---|---|---|---|---|"]
    for group, files in groups.items():
        rows = [r for f in files for r in json.loads(f.read_text())]

        def mean(metric: str) -> str:
            vals = [r["diagnostics"][metric]["value"] for r in rows if metric in r.get("diagnostics", {}) and r["diagnostics"][metric].get("value") is not None]
            return f"{sum(vals) / len(vals):.3f}" if vals else "n/a"

        ok = sum(r["outcome"]["verdict"] == "success" for r in rows)
        md.append(f"| {group} | {len(rows)} | {ok}/{len(rows)} | {mean('tool_call_validity')} | {mean('tool_call_f1_name')} | {mean('redundant_tool_calls')} | {mean('agent_loop_detection')} |")
    out_md = args.runs / f"report_{args.label}" / "auditkit.md"
    out_md.write_text("\n".join(md) + "\n")
    print(out_md.read_text())
