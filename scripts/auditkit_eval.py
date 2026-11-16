"""AuditKIT tool-call and outcome numbers for saved episodes.

Usage: python scripts/auditkit_eval.py --episodes runs/<run_id>/eval/round2_candidate.jsonl --profile full

Input is a JSONL written by the evaluator or by Experiment 0: one episode per line with `conversation`,
`task_id` and the ground-truth verdict `G`. Offline: no judge model, no GPU.
The verified outcome is our ground truth G, passed in as a CustomPredicate. The gold tool route is the scripted
teacher's route (list_tables, run_query with the gold SQL, submit with the gold SQL), scored by tool name.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from auditkit.agent_eval import AgentCase, AgentEvalRunner, AgentEvalSpec, CustomPredicate, episode_from_openai_messages

from healgap.env.dataset import load_dataset
from healgap.env.tools import TOOL_NAMES

SCORERS = ["tool_call_validity", "tool_call_f1_name", "redundant_tool_calls", "agent_loop_detection"]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episodes", type=Path, required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    ds = load_dataset(args.profile)
    recs = [json.loads(line) for line in args.episodes.read_text().splitlines() if line.strip()]
    verdict, episodes, cases = {}, [], []
    for i, r in enumerate(recs):
        cid = f"{r['task_id']}#{i}"
        task = ds.tasks[r["task_id"]]
        verdict[cid] = bool(r["G"])
        episodes.append(episode_from_openai_messages(r["conversation"], case_id=cid))
        route = [[{"name": "list_tables", "arguments": {}}], [{"name": "run_query", "arguments": {"sql": task.gold_sql}}], [{"name": "submit", "arguments": {"sql": task.gold_sql}}]]
        cases.append(AgentCase(id=cid, task=task.question, allowed_tools=list(TOOL_NAMES), reference_turns=route, outcome=CustomPredicate(lambda ep, case: verdict[case.id], version="healgap-G-v1")))
    result = AgentEvalRunner().run(AgentEvalSpec(cases=cases, mode="recorded", episodes=episodes, scorers=SCORERS))
    summary = result.summary()
    print(summary)
    out = args.out or args.episodes.parent.parent / "auditkit" / args.episodes.stem
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".txt").write_text(summary + "\n")
    rows = [getattr(row, "to_dict", lambda row=row: vars(row))() for row in result.rows]
    out.with_suffix(".json").write_text(json.dumps(rows, indent=1, default=str))
