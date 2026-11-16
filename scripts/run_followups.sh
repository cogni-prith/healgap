#!/usr/bin/env bash
# After the main reduced runs: Experiment 0 again under the final environment, then two extra arms, arm by arm.
until grep -q "ALL DONE" runs/logs/reduced_progress.log 2>/dev/null; do sleep 20; done
for s in 0 1 2; do .venv/bin/python scripts/exp0_base_rates.py --config configs/reduced.yaml --seed "$s" --conditions neutral > "runs/logs/exp0_env3_seed$s.log" 2>&1; done
echo "$(date +%H:%M) EXP0 ENV3 DONE" >> runs/logs/reduced_progress.log
for arm in iso_from_start filter_oracle; do
  for s in 0 1 2; do
    .venv/bin/python scripts/run_heal.py --config "configs/arm_$arm.yaml" --seed "$s" > "runs/logs/heal_reduced_${arm}_seed$s.log" 2>&1
    echo "$(date +%H:%M) seed=$s arm=$arm exit=$?" >> runs/logs/reduced_progress.log
  done
done
echo "$(date +%H:%M) FOLLOWUPS DONE" >> runs/logs/reduced_progress.log
