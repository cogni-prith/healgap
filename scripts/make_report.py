"""Tables and figures from saved runs. Usage: python scripts/make_report.py --runs runs/ --label reduced

Reads only files under runs/. Every number in the output traces to runs/<run_id>/eval/*.jsonl or an exp0 run.
Arms with fewer than 3 completed seeds are listed but marked, and are not plotted (hard rule 3).
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from healgap.env.dataset import load_dataset
from healgap.env.tools import episode_from_conversation
from healgap.eval.metrics import EXPLOITS, bootstrap_ci, compute, is_hack
from healgap.eval.score import score_rows

MIN_SEEDS = 3
N_BOOT = 1000


def _load_jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


_DS: dict = {}


def _slim(r: dict) -> dict:
    """Drop the conversation, after recomputing W, G and the exploit label from it with the current verifiers and
    labeller. Stored detector flags (F, F_rule) are kept as recorded at run time."""
    ds = _DS["ds"]
    row = {"episode": episode_from_conversation(r["conversation"]), "steps": r["steps"], "tool_calls": r["tool_calls"], "tool_errors": r["tool_errors"]}
    fresh = score_rows([row], ds, r["seed"])[0]
    return {**{k: v for k, v in r.items() if k != "conversation"}, "W": fresh["W"], "G": fresh["G"], "label": fresh["label"]}


def stats(records: list[dict]) -> dict:
    """Section 8 metrics, plus the same hack split against D_rule so arms with different detectors are comparable."""
    m = compute(records)
    n = len(records)
    m["reported_rule"] = sum(r["F_rule"] for r in records) / n
    m["undetected_rule"] = sum(is_hack(r) and not r["F_rule"] for r in records) / n
    return m


def ci(records: list[dict], key: str) -> str:
    v = stats(records)[key]
    if v is None:
        return "n/a"
    b = bootstrap_ci(records, lambda rs: stats(rs)[key] if rs else None, N_BOOT, seed=0)
    return f"{v:.3f} [{b[0]:.3f}, {b[1]:.3f}]" if b else f"{v:.3f}"


def diff_ci(a: list[dict], b: list[dict], key: str) -> str:
    """stat(a) - stat(b) with a paired 95% bootstrap interval: the same resampled seeds and tasks for both."""
    import random

    rng = random.Random(0)
    seeds = sorted({r["seed"] for r in a})
    tasks = sorted({r["task_id"] for r in a})
    cells: list[dict[tuple, list[dict]]] = []
    for recs in (a, b):
        c: dict[tuple, list[dict]] = defaultdict(list)
        for r in recs:
            c[(r["seed"], r["task_id"])].append(r)
        cells.append(c)
    point = stats(a)[key] - stats(b)[key]
    vals = []
    for _ in range(N_BOOT):
        ss, ts = rng.choices(seeds, k=len(seeds)), rng.choices(tasks, k=len(tasks))
        sa = [r for x in ss for t in ts for r in cells[0].get((x, t), [])]
        sb = [r for x in ss for t in ts for r in cells[1].get((x, t), [])]
        if sa and sb:
            vals.append(stats(sa)[key] - stats(sb)[key])
    vals.sort()
    return f"{point:+.3f} [{vals[int(0.025 * len(vals))]:+.3f}, {vals[int(0.975 * len(vals))]:+.3f}]"


def heal_runs(runs: Path, label: str) -> dict[str, dict[int, Path]]:
    """arm -> seed -> run dir, completed runs only, latest run wins."""
    out: dict[str, dict[int, Path]] = defaultdict(dict)
    for d in sorted(runs.glob(f"heal_{label}_*")):
        man = json.loads((d / "manifest.json").read_text())
        if man.get("status") == "completed":
            out[man["config"]["arm"]["name"]][man["seed"]] = d
    return out


def deployed_records(run: Path) -> dict[int, list[dict]]:
    """round -> eval records of the policy deployed after that round (round 0 is the base model)."""
    out = {0: [_slim(r) for r in _load_jsonl(run / "eval" / "round0_start.jsonl")]}
    for st in json.loads((run / "state.json").read_text()):
        name = "round0_start" if st["deployed"] == "start" else st["deployed"]
        out[st["round"]] = [_slim(r) for r in _load_jsonl(run / "eval" / f"{name}.jsonl")]
    return out


def candidate_records(run: Path) -> dict[int, list[dict]]:
    out = {0: [_slim(r) for r in _load_jsonl(run / "eval" / "round0_start.jsonl")]}
    for p in sorted((run / "eval").glob("round*_candidate.jsonl")):
        out[int(p.name.split("_")[0].removeprefix("round"))] = [_slim(r) for r in _load_jsonl(p)]
    return out


KEYS = [("true_success", "true success"), ("weak_success", "weak success"), ("true_hack_rate", "true hack rate H"), ("false_pass_rate", "false-pass rate"), ("reported_rule", "reported by D_rule"), ("undetected_rule", "undetected by D_rule"), ("reported_hack_rate", "reported by arm detector"), ("undetected_hack_rate", "U (arm detector)")]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=Path, default=Path("runs"))
    ap.add_argument("--label", default="reduced")
    ap.add_argument("--profile", default="full")
    args = ap.parse_args()
    _DS["ds"] = load_dataset(args.profile)
    out = args.runs / f"report_{args.label}"
    out.mkdir(parents=True, exist_ok=True)
    md: list[str] = [f"# healgap report tables ({args.label} profile)", ""]

    # ---- Experiment 0
    exp0 = defaultdict(list)
    for d in sorted(args.runs.glob("exp0_*")):
        man = json.loads((d / "manifest.json").read_text())
        if man.get("status") == "completed" and man["label"] == args.label and man["config"].get("limit") is None:
            for p in d.glob("episodes_*.jsonl"):
                env = man["config"].get("env_version", 1)
                exp0[f"{p.stem.removeprefix('episodes_')} (environment v{env})"] += [dict(_slim(r), run=d.name) for r in _load_jsonl(p)]
    if exp0:
        md += ["## Experiment 0: base rates before any training", "", "Counts are episodes. A hack is W and not G with an exploit label.", "", "| condition | seeds | episodes | OK | " + " | ".join(f"{e} hacks" for e in EXPLOITS) + " | false pass, no exploit label | no submit | weak success | true success | true success easy / medium / hard |", "|---|---|---|---|" + "---|" * (len(EXPLOITS) + 5)]
        for cond, recs in exp0.items():
            n = len(recs)
            tiers = " / ".join(f"{sum(r['G'] for r in recs if r['tier'] == t)}/{sum(r['tier'] == t for r in recs)}" for t in ("easy", "medium", "hard"))
            hacks = " | ".join(str(sum(is_hack(r) and r["label"] == e for r in recs)) for e in EXPLOITS)
            md.append(f"| {cond} | {len({r['seed'] for r in recs})} | {n} | {sum(r['label'] == 'OK' for r in recs)} | {hacks} | {sum(r['W'] and not r['G'] and r['label'] == 'ERR' for r in recs)} | {sum(not r['submitted'] for r in recs)} | {sum(r['W'] for r in recs) / n:.3f} | {sum(r['G'] for r in recs) / n:.3f} | {tiers} |")
        md.append("")

    # ---- Heal runs
    arms = heal_runs(args.runs, args.label)
    plotted = {}
    for kind, loader in (("deployed", deployed_records), ("candidate", candidate_records)):
        md += [f"## Heal loop, {kind} policy per round", "", "Mean with 95% bootstrap interval over seeds and tasks. Round 0 is the starting policy.", ""]
        for arm, seeds in arms.items():
            per_round: dict[int, list[dict]] = defaultdict(list)
            for run in seeds.values():
                for rnd, recs in loader(run).items():
                    per_round[rnd] += recs
            ok = len(seeds) >= MIN_SEEDS
            md += [f"### {arm}: {len(seeds)} seed(s) {sorted(seeds)}" + ("" if ok else f" (fewer than {MIN_SEEDS} seeds: not a reportable result)"), "", "| round | n | " + " | ".join(k[1] for k in KEYS) + " | exploit counts among hacks |", "|---|---|" + "---|" * (len(KEYS) + 1)]
            for rnd in sorted(per_round):
                recs = per_round[rnd]
                mix = ", ".join(f"{e}:{sum(is_hack(r) and r['label'] == e for r in recs)}" for e in EXPLOITS)
                md.append(f"| {rnd} | {len(recs)} | " + " | ".join(ci(recs, k[0]) for k in KEYS) + f" | {mix} |")
            md.append("")
            if ok and kind == "deployed":
                plotted[arm] = per_round

    # ---- Paired comparisons (deployed policies, arms with enough seeds)
    if plotted:
        last = max(max(pr) for pr in plotted.values())
        md += ["## Paired comparisons", "", f"Difference with a paired 95% bootstrap interval over seeds and tasks. Deployed policies. Last round is round {last}. With 3 seeds these are weak tests: read the intervals, not just the sign.", "", "| comparison | metric | difference |", "|---|---|---|"]
        rows = []
        for arm in plotted:
            for key, name in (("undetected_rule", "undetected by D_rule"), ("reported_rule", "reported by D_rule"), ("true_hack_rate", "true hack rate H"), ("true_success", "true success")):
                rows.append((f"{arm}: round {last} minus round 0", name, plotted[arm][last], plotted[arm][0], key))
                rows.append((f"{arm}: round {last} minus round 1", name, plotted[arm][last], plotted[arm][1], key))
        for x, y in (("filter_rule", "filter_sim"), ("filter_rule", "weak_only"), ("iso_fix", "filter_rule"), ("iso_fix", "weak_only"), ("iso_from_start", "weak_only"), ("filter_oracle", "filter_rule")):
            if x in plotted and y in plotted:
                for key, name in (("undetected_rule", "undetected by D_rule"), ("true_hack_rate", "true hack rate H"), ("true_success", "true success")):
                    rows.append((f"{x} minus {y}, round {last}", name, plotted[x][last], plotted[y][last], key))
        md += [f"| {c} | {n} | {diff_ci(a, b, k)} |" for c, n, a, b, k in rows] + [""]

    # ---- Loop internals
    md += ["## Loop internals per run", "", "| arm | seed | round | signal | collected | kept as positives | flagged | failure types | gate: candidate vs deployed signal success | decision |", "|---|---|---|---|---|---|---|---|---|---|"]
    for arm, seeds in arms.items():
        for seed, run in sorted(seeds.items()):
            for st in json.loads((run / "state.json").read_text()):
                md.append(f"| {arm} | {seed} | {st['round']} | {st['signal']} | {st['n_collected']} | {st['n_kept']} | {st['n_flagged']} | {st['failure_types']} | {st['candidate_gate']['signal_success']:.2f} vs {st['deployed_gate']['signal_success']:.2f} | {st['gate_decision']} |")
    md.append("")

    # ---- Figures (only arms with enough seeds)
    if plotted:
        fig, axes = plt.subplots(1, len(plotted), figsize=(4.2 * len(plotted), 3.6), sharey=True, squeeze=False)
        for ax, (arm, per_round) in zip(axes[0], plotted.items()):
            rounds = sorted(per_round)
            for key, name, color in (("true_hack_rate", "true hack rate H", "tab:red"), ("undetected_rule", "undetected by D_rule", "tab:purple"), ("reported_rule", "reported by D_rule", "tab:blue"), ("true_success", "true success", "tab:green")):
                vals = [stats(per_round[r])[key] for r in rounds]
                cis = [bootstrap_ci(per_round[r], lambda rs, k=key: stats(rs)[k] if rs else None, N_BOOT, seed=0) for r in rounds]
                ax.plot(rounds, vals, marker="o", color=color, label=name)
                ax.fill_between(rounds, [c[0] for c in cis], [c[1] for c in cis], color=color, alpha=0.15)
            ax.set_title(arm)
            ax.set_xlabel("heal round (0 = starting policy)")
            ax.set_xticks(rounds)
        axes[0][0].set_ylabel("rate on held-out eval tasks")
        axes[0][-1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "primary.png", dpi=150)

        fig, axes = plt.subplots(1, len(plotted), figsize=(4.2 * len(plotted), 3.6), sharey=True, squeeze=False)
        for ax, (arm, per_round) in zip(axes[0], plotted.items()):
            rounds = sorted(per_round)
            bottom = [0.0] * len(rounds)
            for e in EXPLOITS:
                vals = [sum(is_hack(r) and r["label"] == e for r in per_round[rnd]) / len(per_round[rnd]) for rnd in rounds]
                ax.bar(rounds, vals, bottom=bottom, label=e)
                bottom = [b + v for b, v in zip(bottom, vals)]
            ax.set_title(arm)
            ax.set_xlabel("heal round")
            ax.set_xticks(rounds)
        axes[0][0].set_ylabel("hack rate by exploit type")
        axes[0][-1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(out / "exploit_mix.png", dpi=150)

    (out / "tables.md").write_text("\n".join(md))
    print(f"wrote {out}/tables.md", "and figures" if plotted else "(no figures: no arm has 3 completed seeds)")


if __name__ == "__main__":
    main()
