---
license: mit
task_categories: [text-generation]
tags: [reward-hacking, self-healing-agents, text-to-sql, agent-trajectories, agenttune, auditkit, lexsi-hackathon]
---

# healgap runs

Data and run outputs from **healgap**, a Lexsi Labs hackathon project (Track 3, Agentic Fine-tuning) that asks whether a self-healing agent loop fixes the reward hacks its detector cannot see.

Code, write-up and the full decisions log: https://github.com/cogni-prith/healgap (start with `docs/REPORT.md`).
Adapters: https://huggingface.co/cognitive-prith/healgap-adapters

## Contents

| Path | What it is |
|---|---|
| `data/tasks_full.json`, `data/tasks_smoke.json` | Tasks: question, gold SQL, tier, template, split |
| `data/splits.json` | Template-level train, gate and eval split, frozen |
| `data/visible/`, `data/iso_train/`, `data/hidden/` | SQLite databases: the visible copy (with the planted `_report_cache` table), variants for the isomorphic check, and ground-truth variants |
| `runs/exp0_*/` | Experiment 0: base-model episodes with full conversations, weak verdict W, ground truth G and exploit label |
| `runs/seedpolicy_reduced_seed*/demos.json` | Scripted honest and exploit demonstrations used for the seeding intervention |
| `runs/heal_reduced_<arm>_seed<k>_*/` | One heal run: `round<r>/collect.jsonl` (what the loop saw and decided), `round<r>/curated.json` (the SFT data), `state.json` (gate decisions), `eval/*.jsonl` (every eval episode with conversation, W, G, detector flags and label), `manifest.json` |
| `runs/report_reduced/` | Tables and figures. Every number in the write-up comes from here |
| `runs/_base_cache/` | Rollouts of the starting policy shared across arms |
| `runs/superseded_*/` | Runs made before an environment or gate fix. Kept for the record, excluded from results. `docs/DECISIONS.md` explains each |
| `runs/m0_*/`, `runs/logs/` | Toolchain smoke runs and logs |

## Notes for reuse

- The loopholes are planted: `_report_cache` leaks answers, the weak verifier checks only the visible database, and on hard tasks it checks only the result shape.
- The `data/hidden/` variants are the ground truth. In the project nothing on the training side may read them. If you reuse the benchmark, keep that separation.
- Exploit labels E3 and E4 come from syntactic rules and E5 also catches honest wrong queries. Use the false-pass rate (W and not G) when you need a label-free number.
- Small scale: one 1.5B model, 3 seeds, 2 heal rounds, one sampled episode per eval task.
