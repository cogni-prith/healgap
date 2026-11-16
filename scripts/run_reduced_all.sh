#!/usr/bin/env bash
# Reduced-profile heal runs: one seeded starting policy per seed, then the arms in priority order.
# All arms for one seed finish before the next seed starts, so a cutoff leaves complete seeds.
# Usage: scripts/run_reduced_all.sh "0 1 2" "weak_only filter_rule filter_sim iso_fix"
SEEDS=${1:-"0 1 2"}
ARMS=${2:-"weak_only filter_rule filter_sim iso_fix"}
mkdir -p runs/logs
for s in $SEEDS; do
  if [ ! -f "runs/seedpolicy_reduced_seed$s/adapter/adapter_config.json" ]; then
    .venv/bin/python scripts/make_seed_policy.py --config configs/reduced.yaml --seed "$s" > "runs/logs/seedpolicy_reduced_seed$s.log" 2>&1
  fi
  for arm in $ARMS; do
    if [ "$arm" = "filter_sim" ] && [ ! -f runs/sim_calibration_reduced.json ]; then
      .venv/bin/python scripts/calibrate_sim.py --config configs/reduced.yaml --seed "$s" > runs/logs/calibrate_sim.log 2>&1
    fi
    .venv/bin/python scripts/run_heal.py --config "configs/arm_$arm.yaml" --seed "$s" > "runs/logs/heal_reduced_${arm}_seed$s.log" 2>&1
    echo "$(date +%H:%M) seed=$s arm=$arm exit=$?" >> runs/logs/reduced_progress.log
  done
done
echo "$(date +%H:%M) ALL DONE" >> runs/logs/reduced_progress.log
