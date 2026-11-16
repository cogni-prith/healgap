## AuditKIT (offline, no judge model)

Per-episode AuditKIT diagnostics averaged over episodes, pooled over seeds. Verified success is AuditKIT's outcome verdict from our ground truth G passed as a CustomPredicate. Tool-call F1 by name is against the scripted teacher's route (list_tables, run_query, submit).

| policy | episodes | verified success | tool-call validity | tool-call F1 (name) | redundant calls (lower is better) | loop-free |
|---|---|---|---|---|---|---|
| filter_oracle: deployed after round 2 | 105 | 58/105 | 1.000 | 0.913 | 0.043 | 0.924 |
| starting policy (seeded) | 105 | 8/105 | 1.000 | 0.990 | 0.000 | 1.000 |
| filter_rule: deployed after round 2 | 105 | 18/105 | 1.000 | 1.000 | 0.000 | 1.000 |
| filter_sim: deployed after round 2 | 105 | 13/105 | 1.000 | 0.968 | 0.020 | 0.943 |
| iso_fix: deployed after round 2 | 105 | 61/105 | 1.000 | 0.952 | 0.019 | 0.971 |
| iso_from_start: deployed after round 2 | 105 | 66/105 | 1.000 | 0.980 | 0.012 | 0.981 |
| weak_only: deployed after round 2 | 105 | 11/105 | 1.000 | 0.946 | 0.024 | 0.943 |
