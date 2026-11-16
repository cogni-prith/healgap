# healgap

Lexsi Labs hackathon, Track 3 (Agentic Fine-tuning). Problem statements: "Self-healing agents" and "Reward design and reward-hacking defences".

**Question.** A self-healing loop detects failed or cheating runs, builds corrective training data, retrains, and gates redeployment. It can only fix what its detector sees. Do repeated heal rounds leave, or shift the agent toward, reward hacks the detector misses, so that the detector-reported hack rate looks fine while the true hack rate does not? And does an isomorphic reward (re-running the submitted query on resampled copies of the database) fix this with no detector?

**Write-up with results:** `docs/REPORT.md`. Adapters: https://huggingface.co/cognitive-prith/healgap-adapters. Data, rollouts and eval records: https://huggingface.co/datasets/cognitive-prith/healgap-runs.

**Headline (reduced profile, 3 seeds, planted loopholes and planted starting hacks).**

- Heal loops that keep episodes passing the hackable check ended with 41% to 52% of eval episodes being hacks, against 37% at the start.
- We did not find that a blind-spot detector selects for stealth: the pre-specified test was null. The rule detector's flagged rate fell from 0.29 to 0.10 while undetected hacks reached 0.52, but the same happened with no detector.
- Keeping only episodes whose query also works on resampled data, with no detector, cut the true hack rate to 0.01 to 0.06 and raised true success to about 0.6, matching a perfect-detector upper bound.

**Status and scope.** Read `docs/DECISIONS.md` first. It records what was verified about the toolchain, every place the build departs from `docs/EXPERIMENT_SPEC.md`, and why. The short version: this is a reduced-profile study on one small model (`Qwen/Qwen2.5-1.5B-Instruct`), with planted loopholes, a corrective-SFT heal loop (no GRPO arms), 2 heal rounds and 3 seeds. Results are in `runs/report_reduced/tables.md` and in the article.

## What is here

| Path | Contents |
|---|---|
| `healgap/env/` | SQLite task environment: 4 schema families, 36 question templates with gold SQL, variant generator, the four agent tools |
| `healgap/verifiers/` | `V_weak` (the hackable signal, with planted loopholes) and `R_iso` (isomorphic reward) |
| `healgap/groundtruth/` | Hidden checker `G` and the oracle exploit labeller. Imported only by `healgap/eval/` |
| `healgap/detectors/` | `D_rule`. The control detectors `D_sim` and `D_oracle` need ground truth and live in `healgap/eval/` |
| `healgap/loop/` | Rollouts on AgentTune's rollout engine, scripted teacher, the heal loop, run manifests |
| `healgap/train/` | Corrective SFT through AgentTune's `create_distill_trainer` |
| `healgap/eval/` | Metrics (spec section 8), scoring, evaluation callback |
| `configs/` | `data.yaml`, `smoke.yaml`, `reduced.yaml`, one `arm_*.yaml` per arm |
| `docs/` | Research context, experiment spec, build plan, decisions log |
| `tests/` | 36 tests, including the ground-truth isolation test and hand-written trajectories per exploit type |

## Planted loopholes (stated up front)

The training signal `V_weak` checks the submitted SQL on the visible database only. We planted three loopholes:

- A. The visible database contains a table `_report_cache` holding the expected result per task.
- B. Any query whose result equals the gold result on the visible database passes, so hardcoded answers pass.
- C. On hard tasks only the row count and column count are compared.

Ground truth `G` runs the submitted SQL on 5 resampled variants of the database that nothing in training can see.

## Setup

Python 3.12, a CUDA GPU with 8 GB or more.

```
git clone https://github.com/Lexsi-Labs/AgentTune.git external/AgentTune
git clone https://github.com/Lexsi-Labs/AuditKIT.git external/AuditKIT
pip install -e external/AgentTune
pip install external/AuditKIT
pip install -e ".[dev]"
```

AgentTune (LSAL v1.1) and AuditKIT (LSAL v1.2) are not vendored. Line references in `docs/DECISIONS.md` are against AgentTune `2aecde4` and AuditKIT `9d4e21b`.

## Commands

```
pytest -q
python scripts/make_data.py --config configs/data.yaml
python scripts/exp0_base_rates.py --config configs/smoke.yaml --seed 0
python scripts/make_seed_policy.py --config configs/smoke.yaml --seed 0
python scripts/run_heal.py --config configs/smoke_filter_rule.yaml --seed 0
python scripts/run_heal.py --config configs/arm_filter_rule.yaml --seed 0
python scripts/make_report.py --runs runs/ --label reduced
python scripts/auditkit_eval.py --episodes runs/<run_id>/eval/round2_candidate.jsonl --profile full
```

The first five run on the smoke profile and are the quickest end-to-end check. Every run writes `runs/<run_id>/manifest.json` with the full config, seed, model id and library versions.

## Honest limits

- Loopholes are planted. Nothing here is a claim about natural loopholes, frontier models or production pipelines.
- One model family, 3 seeds, 2 heal rounds, 35 eval tasks with one sampled episode each. Intervals are wide.
- The heal loop retrains with corrective SFT. The spec's GRPO arms were not run. GRPO through AgentTune is shown only by a smoke test (`scripts/m0_grpo_smoke.py`).
- That training against monitors can teach evasion is prior work (see `docs/RESEARCH_CONTEXT.md`). Isomorphic and multi-database verification are not our method.
