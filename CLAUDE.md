# CLAUDE.md

Project: **healgap**. Lexsi Labs hackathon, Track 3 (Agentic Fine-tuning).
Team: Prithwish (environment, loop, detectors, evaluation) and Rupam (RL training, reward design).

Read these before writing any code, in this order:

1. `docs/RESEARCH_CONTEXT.md` (the question, what is and is not novel, what we may claim)
2. `docs/EXPERIMENT_SPEC.md` (environment, loopholes, detectors, arms, metrics)
3. `docs/BUILD_PLAN.md` (milestones with acceptance checks)

## One-paragraph summary

A self-healing agent loop detects failed or cheating runs, builds corrective training data, retrains, and gates redeployment. The loop can only fix what its detector sees. We test whether repeated heal rounds shift a tool-using SQL agent toward reward hacks the detector misses, so that the detector-reported hack rate falls while the true hack rate does not. We then test whether an isomorphic reward (re-running the agent's submitted query on resampled copies of the database) removes the problem without needing any detector.

Problem statements covered: "Self-healing agents" and "Reward design and reward-hacking defences".

## Hard rules

These are research-integrity rules. Breaking one invalidates results.

1. **Ground truth isolation.** Nothing under `healgap/groundtruth/` or `data/hidden/` may be imported, read, or logged by the agent, the weak verifier, any detector, the corrective-data generator, the trainer, or the deployment gate. Only `healgap/eval/` may import it. Enforce with a test (`tests/test_isolation.py`) that scans imports.
2. **Variant pool separation.** Database variants used by the isomorphic reward (`data/iso_train/`) and variants used by ground truth (`data/hidden/`) come from disjoint seeds. Assert this at load time.
3. **No result is reported from one seed.** Minimum 3 seeds for any number that goes in the report. Smoke runs are labelled smoke and never plotted with real runs.
4. **Never fabricate.** If a run did not happen, a metric was not computed, or an API was not verified, say so. No placeholder numbers in tables, README, or the report. Unknown AgentTune or AuditKIT behaviour is checked against the cloned repo docs, not guessed.
5. **Do not tune on eval tasks.** Task split is fixed in `data/splits.json` at M1 and not changed afterwards.
6. **Every run writes a manifest.** `runs/<run_id>/manifest.json` with git commit, full config, seed, model id, library versions, and start and end time.
7. **Negative results are results.** If hacks never get stealthier, that is the finding. Do not adjust the setup after seeing results to produce the hoped-for curve. Any post-hoc change is logged in `docs/DECISIONS.md` with the reason and date.

## Hackathon constraints

- Must use the Lexsi toolchain: **AgentTune** for training, **AuditKIT** for evaluation. Only the last submission before the deadline counts.
- AgentTune license is LSAL v1.1 (source-available, noncommercial research is allowed). Do not vendor its source into this repo. Install it as a dependency.
- AgentTune needs Python 3.12+, PyTorch 2.11, transformers 5.15 or later. vLLM is optional and Linux + CUDA only.

## What is verified about AgentTune (from its README, 2026-11-15)

Verified:

- Install: `git clone https://github.com/Lexsi-Labs/AgentTune.git` then `pip install -e .` inside it.
- `from agenttune.agentic import Project, DictToolHarness, ReActStrategy`
- `create_agentic_trainer(algorithm="grpo"|"ppo"|"dpo"|"rloo"|"bco", model=..., train_dataset=..., tools=[...], reward_funcs=[...], output_dir=...)` then `trainer.train()`. Runs on the TRL backend.
- `train_dataset` is a Hugging Face `Dataset`. Each row has `prompt` (chat-message list). Extra columns such as `answer` reach reward functions as keyword arguments.
- Custom reward signature: `def r(prompts, completions, answer=None, **kwargs) -> list[float]`, one float per completion. `combine_rewards(...)` does weighted composition. `LLMJudge` lives in `agenttune.agentic.rewards.llm_judge`.
- `tools=` takes plain typed Python functions or `BaseTool` objects. `SQLDatabaseTool("sqlite:///path.db")` exists in `agenttune.agentic.tools.builtin.sql` with `.execute(action="sql_db_query", input=sql)` returning `.success`, `.output`, `.error`.
- `create_distill_trainer(student=..., demonstrations=[(input, target), ...] | trajectories=..., output_dir=..., num_train_epochs=..., learning_rate=...)` does LoRA SFT (behaviour cloning).
- Closed loop lives in `agenttune.decide.closed_loop` with `FailureDetector`, `FailureClassifier`, `TrainingExampleGenerator`, `RetrainingTrigger`, `DeploymentGate`.
- EventLog is the shared trajectory schema with `light` and `full` tiers.
- Example models: `Qwen/Qwen3-1.7B`, `Qwen/Qwen2.5-1.5B-Instruct`, `HuggingFaceTB/SmolLM2-360M-Instruct`.

Not verified, check in M0 before depending on it:

- Method signatures of the five `closed_loop` classes, and whether they accept custom detectors and custom gates.
- Whether a custom reward callable can see the full tool trajectory (we need the submitted SQL and the list of tool calls), or only the final completion text.
- Whether per-episode metadata (task id, database id) reaches the reward function.
- Everything about AuditKIT's API. Read its docs first.

If a needed hook is missing, wrap rather than fork: keep our own thin loop in `healgap/loop/` that calls AgentTune trainers, and record the gap in `docs/DECISIONS.md`.

## Repo layout

```
healgap/
  env/            SQLite task environment, tools, task and database generators
  verifiers/      weak verifier (the hackable training signal), isomorphic verifier
  groundtruth/    hidden checker and oracle exploit labeller (eval only, see rule 1)
  detectors/      rule, judge, simulated (random-miss), oracle, optional probe
  loop/           heal rounds: collect, detect, classify, generate, retrain, gate
  train/          AgentTune wrappers, reward functions, configs
  eval/           metrics, AuditKIT integration, plots
configs/          one YAML per arm, plus smoke.yaml and full.yaml profiles
data/             generated databases and task files (visible, iso_train, hidden)
runs/             run outputs, one folder per run id
docs/             research context, spec, plan, decisions log
tests/
scripts/
```

## Commands

Keep every command on one line. No backslash continuations.

- Install: `pip install -e .`
- Tests: `pytest -q`
- Generate data: `python scripts/make_data.py --config configs/data.yaml`
- Base-rate check (Experiment 0): `python scripts/exp0_base_rates.py --config configs/smoke.yaml`
- One heal run: `python scripts/run_heal.py --config configs/arm_filter_rule.yaml --seed 0`
- Evaluate a run: `python scripts/evaluate.py --run runs/<run_id>`
- Plots and tables: `python scripts/make_report.py --runs runs/`

## Working conventions

- When modifying code, output the complete final file, not a diff or snippet.
- Type hints everywhere. Small pure functions for verifiers, detectors, and metrics, each with unit tests on hand-written trajectories.
- All randomness goes through an explicit seed passed down from the config. No global seeding inside library code.
- Config in YAML, loaded into dataclasses. No magic constants in code.
- Log trajectories as JSONL in AgentTune EventLog format where possible so AuditKIT can read them.
- Prose in docs and the report: plain and direct, no em-dashes, no buzzword lists.
- Build in milestone order. Do not start a milestone until the previous one passes its acceptance check. Run the smoke profile end to end before any full run.
- Ask before: changing the task split, changing a metric definition, adding a dependency over 1 GB, or launching anything expected to take more than 2 GPU-hours.

## Open inputs from the team (ask if not in `docs/DECISIONS.md`)

- Submission deadline.
- GPU available (model and VRAM) and total GPU-hours. This sets the base model (default `Qwen/Qwen3-1.7B`, larger only if budget allows) and how many arms run.
- Whether an API judge model is allowed and funded, or the judge must be local.
- Confirmation from Lexsi (Discord `#report-issues`) that a research-style submission with a negative-result possibility is in scope.
