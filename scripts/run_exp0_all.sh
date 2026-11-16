#!/usr/bin/env bash
# Experiment 0 on the reduced profile. Seed 0 ran all three prompt conditions (run separately).
# Seeds 1 and 2 run the neutral condition only: the hint conditions were cut for time (docs/DECISIONS.md, 2026-11-16).
for s in 1 2; do .venv/bin/python scripts/exp0_base_rates.py --config configs/reduced.yaml --seed "$s" --conditions neutral > "runs/logs/exp0_reduced_seed$s.log" 2>&1; done
date > runs/logs/exp0_reduced.done
