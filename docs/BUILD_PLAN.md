# Build plan

Work in order. Each milestone has an acceptance check. Do not start the next one until the check passes. Owner in brackets: P = Prithwish, R = Rupam. Claude Code can work on either side but should keep the two tracks mergeable.

## M0. Toolchain check (half a day) [P + R]

- Create the repo skeleton from `CLAUDE.md`, `pyproject.toml`, Python 3.12.
- Clone and install AgentTune. Run its no-GPU quickstart (`Project`, `DictToolHarness`, `ReActStrategy`).
- Read `docs/concepts/decide-and-closed-loop.md`, `docs/algorithms/overview.md`, and `src/agenttune/agentic/README.md` in the AgentTune repo. Read the AuditKIT docs.
- Answer in `docs/DECISIONS.md`, with file and line references:
  1. Can a custom reward function see the tool trajectory and per-episode metadata (task id, database path)? If not, what is the workaround (for example encode the submitted SQL in the final completion and parse it, and pass task id as a dataset column)?
  2. Do `FailureDetector` and `DeploymentGate` accept custom logic? If not, we wrap our own loop and call the trainers.
  3. What does AuditKIT need as input, and which of our metrics can it compute or host?
  4. Does GRPO in AgentTune expose KL or a reference-policy term?
- Run a 5-minute GRPO smoke on SmolLM2-360M with a trivial tool and custom reward to prove the training path works end to end.

Accept when: the quickstart and the GRPO smoke both run, and the four questions have written answers.

## M1. Environment and data [P]

- Schema families, data generator, variant generator (resample plus identifier permutation), question templates with gold SQL in three tiers.
- Tools: `list_tables`, `describe_table`, `run_query`, `submit`. Read-only connection, row cap, timeout.
- Loophole A table `_report_cache` in visible databases only.
- `data/splits.json` with template-level train, gate, and eval splits. Freeze it.
- Tests: gold SQL runs on every database and variant; every task has at least one distinguishing variant in both pools; iso_train and hidden seeds are disjoint; `_report_cache` is absent from all variants.

Accept when: `python scripts/make_data.py --config configs/data.yaml` produces the smoke and full datasets and `pytest -q` passes.

## M2. Verifiers, ground truth, oracle labeller, metrics [P]

- `V_weak` with loopholes B and C. `R_iso`. `G`. Oracle exploit labeller for E1 to E5, ERR, OK.
- Metrics module implementing section 8 of the spec exactly, with bootstrap CIs.
- Hand-write at least two trajectories per exploit type plus honest success and honest error. Unit-test every verifier, the labeller, and every metric against them.
- `tests/test_isolation.py`: fails if anything outside `healgap/eval/` imports `healgap/groundtruth/` or reads `data/hidden/`.

Accept when: all hand-written trajectories get the expected W, G, R_iso, label, and metric values.

## M3. Agent rollout and Experiment 0 [P, R reviews]

- Rollout harness on AgentTune (`Project` plus harness), EventLog JSONL output, batched generation.
- `scripts/exp0_base_rates.py` per spec section 9.
- Write the result table and the decision into `docs/DECISIONS.md`.

Accept when: base rates per exploit type and per prompt condition are recorded with counts, and the proceed, hint, or escalate decision is written down. This is a hard gate. If the decision is escalate, stop and ask the team.

## M4. Training wrappers and rewards [R]

- Reward functions in AgentTune's callable signature: weak reward, weak reward with detector penalty, weak reward with screening (dropped rollouts), isomorphic reward. Each unit-tested on the M2 hand-written trajectories.
- GRPO wrapper and corrective-SFT wrapper that continue from a given adapter and write a new one.
- A0 for one round on the smoke profile.

Accept when: one smoke round of A0 trains, saves an adapter, reloads it, and weak success on train tasks moves in the expected direction. Confirm the reward the trainer logged matches an offline recomputation on the saved rollouts for at least 50 episodes.

## M5. Detectors and the heal loop [P]

- D_rule, D_sim(r), D_oracle, D_judge. Optional D_probe later.
- Loop driver: collect, detect, classify, generate corrective data with the scripted teacher, retrain, gate, evaluate. Resumable per round. Manifest per run.
- Arm configs A0 to A5.
- Measure D_rule recall per exploit type on Experiment 0 rollouts and set r for D_sim.

Accept when: the smoke profile runs 2 rounds end to end for A0, A2 with D_rule, and A4, producing metrics files and no isolation-test failures.

## M6. Full runs [R runs training, P runs evaluation]

- Run the priority list from spec section 7 in order, 3 seeds each. Stop at the budget line agreed with the team.
- After lines 1 and 2 finish for one seed, look at the curves only to check for bugs (for example reward always 0, adapters not loading). Do not change the design based on the direction of the effect.

Accept when: lines 1 to 4 have 3 complete seeds each with manifests.

## M7. Analysis, AuditKIT, report [P + R]

- `scripts/make_report.py`: primary and secondary figures, per-arm tables with CIs, detector recall per exploit type per round, 6 to 10 example transcripts (one per exploit type, plus honest runs).
- Run the final policies through AuditKIT for tool-call accuracy and reliability numbers, as the track expects.
- Report sections: question, related work and what is not new, setup (planted loopholes stated up front), results per hypothesis including any that failed, threats to validity, reproduction commands.
- README with one-line commands to regenerate data, run smoke, and rebuild figures from saved runs.

Accept when: every number in the report traces to a file under `runs/`, and a fresh clone can run the smoke profile from the README.

## Stretch, only after M7

- D_probe as a gate-only detector.
- LLM teacher for corrective data.
- Fractional-credit isomorphic reward ablation.
- Recontextualization or inoculation arm for comparison with prompt-level fixes.
- A second base model.

## Things that commonly go wrong here

- The reward function silently returns 0 for every episode because SQL parsing of the completion fails. Log the parse-failure rate.
- The agent never calls `submit` within the step limit. Track it as its own failure type and count it in true success as a failure.
- Adapters stack or reset by accident between rounds. Assert the parent adapter id in the manifest.
- Eval sampling temperature differs from training. Fix both in config.
- A variant where gold and visible answers coincide makes hardcoding look correct. The M1 test covers this; keep it.
- Detector false positives on honest long queries poison the corrective data. Report precision, not only recall.
