#!/usr/bin/env bash
# Upload run artifacts to the Hugging Face Hub. Usage: scripts/publish_hf.sh <hf-username>
# Models: LoRA adapters of the seeded starting policies and of every heal round.
# Dataset: generated tasks and databases, all run outputs except adapter weights, and the report.
set -u
NS=${1:?usage: scripts/publish_hf.sh <hf-username>}
HF=.venv/bin/hf

$HF upload "$NS/healgap-adapters" docs/MODEL_CARD.md README.md --repo-type model --commit-message "model card"
$HF upload "$NS/healgap-adapters" runs . --repo-type model --include "seedpolicy_reduced_seed*/adapter/*" --include "seedpolicy_reduced_seed*/manifest.json" --include "heal_reduced_*/round*/adapter/*" --include "heal_reduced_*/manifest.json" --include "heal_reduced_*/state.json" --exclude "*/checkpoint-*/*" --commit-message "LoRA adapters: seeded starting policies and heal rounds"

$HF upload "$NS/healgap-runs" docs/DATASET_CARD.md README.md --repo-type dataset --commit-message "dataset card"
$HF upload "$NS/healgap-runs" data data --repo-type dataset --commit-message "tasks, split, databases"
$HF upload "$NS/healgap-runs" runs runs --repo-type dataset --exclude "*/adapter/*" --exclude "*.safetensors" --exclude "*.bin" --exclude "*/checkpoint-*/*" --commit-message "run outputs: rollouts, eval records, manifests, report"
