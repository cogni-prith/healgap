# healgap report tables (reduced profile)

## Experiment 0: base rates before any training

Counts are episodes. A hack is W and not G with an exploit label.

| condition | seeds | episodes | OK | E1 hacks | E2 hacks | E3 hacks | E4 hacks | E5 hacks | false pass, no exploit label | no submit | weak success | true success | true success easy / medium / hard |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hint_check (environment v1) | 1 | 80 | 5 | 0 | 0 | 0 | 0 | 0 | 3 | 65 | 0.100 | 0.062 | 0/28 / 5/27 / 0/25 |
| hint_cache (environment v1) | 1 | 80 | 4 | 0 | 0 | 0 | 0 | 0 | 2 | 69 | 0.075 | 0.050 | 0/28 / 4/27 / 0/25 |
| neutral (environment v1) | 3 | 240 | 46 | 0 | 0 | 0 | 0 | 2 | 4 | 162 | 0.217 | 0.192 | 9/84 / 36/81 / 1/75 |
| neutral (environment v3) | 3 | 240 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 240 | 0.000 | 0.000 | 0/84 / 0/81 / 0/75 |

## Heal loop, deployed policy per round

Mean with 95% bootstrap interval over seeds and tasks. Round 0 is the starting policy.

### filter_oracle: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.371 [0.257, 0.505] | 0.000 [0.000, 0.000] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.533 [0.390, 0.676] | 0.562 [0.438, 0.686] | 0.029 [0.000, 0.076] | 0.029 [0.000, 0.076] | 0.048 [0.000, 0.143] | 0.029 [0.000, 0.076] | 0.029 [0.000, 0.076] | 0.000 [0.000, 0.000] | E1:0, E2:0, E3:0, E4:2, E5:1 |
| 2 | 105 | 0.552 [0.429, 0.676] | 0.590 [0.486, 0.695] | 0.038 [0.000, 0.095] | 0.038 [0.000, 0.095] | 0.029 [0.000, 0.095] | 0.029 [0.000, 0.076] | 0.038 [0.000, 0.095] | 0.000 [0.000, 0.000] | E1:0, E2:1, E3:0, E4:1, E5:2 |

### filter_rule: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.114 [0.038, 0.210] | 0.638 [0.486, 0.790] | 0.505 [0.362, 0.657] | 0.524 [0.381, 0.676] | 0.124 [0.038, 0.238] | 0.505 [0.362, 0.657] | 0.124 [0.038, 0.238] | 0.505 [0.362, 0.657] | E1:0, E2:0, E3:0, E4:53, E5:0 |
| 2 | 105 | 0.171 [0.086, 0.276] | 0.724 [0.619, 0.819] | 0.524 [0.390, 0.667] | 0.552 [0.410, 0.695] | 0.095 [0.000, 0.229] | 0.524 [0.390, 0.667] | 0.095 [0.000, 0.229] | 0.524 [0.390, 0.667] | E1:0, E2:0, E3:0, E4:55, E5:0 |

### filter_sim: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.219 [0.143, 0.305] | 0.286 [0.181, 0.410] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.076 [0.029, 0.133] | 0.552 [0.438, 0.676] | 0.457 [0.352, 0.571] | 0.476 [0.371, 0.600] | 0.219 [0.105, 0.352] | 0.410 [0.295, 0.524] | 0.152 [0.057, 0.267] | 0.390 [0.295, 0.495] | E1:0, E2:5, E3:0, E4:43, E5:0 |
| 2 | 105 | 0.124 [0.057, 0.210] | 0.543 [0.429, 0.667] | 0.410 [0.314, 0.505] | 0.419 [0.314, 0.524] | 0.133 [0.029, 0.248] | 0.381 [0.276, 0.486] | 0.152 [0.067, 0.257] | 0.352 [0.248, 0.467] | E1:0, E2:3, E3:0, E4:40, E5:0 |

### iso_fix: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.181 [0.095, 0.267] | 0.667 [0.552, 0.771] | 0.467 [0.352, 0.581] | 0.486 [0.371, 0.600] | 0.048 [0.010, 0.095] | 0.467 [0.352, 0.581] | 0.048 [0.010, 0.095] | 0.467 [0.352, 0.581] | E1:0, E2:0, E3:0, E4:48, E5:1 |
| 2 | 105 | 0.581 [0.457, 0.724] | 0.590 [0.457, 0.733] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | E1:0, E2:0, E3:0, E4:0, E5:1 |

### iso_from_start: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.000 [0.000, 0.000] | 0.371 [0.257, 0.505] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.629 [0.495, 0.771] | 0.667 [0.524, 0.829] | 0.038 [0.000, 0.086] | 0.038 [0.000, 0.086] | 0.000 [0.000, 0.000] | 0.038 [0.000, 0.086] | 0.000 [0.000, 0.000] | 0.038 [0.000, 0.086] | E1:0, E2:0, E3:0, E4:0, E5:4 |
| 2 | 105 | 0.629 [0.486, 0.771] | 0.686 [0.533, 0.829] | 0.057 [0.000, 0.124] | 0.057 [0.000, 0.124] | 0.000 [0.000, 0.000] | 0.057 [0.000, 0.124] | 0.000 [0.000, 0.000] | 0.057 [0.000, 0.124] | E1:0, E2:0, E3:0, E4:0, E5:6 |

### weak_only: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.000 [0.000, 0.000] | 0.371 [0.257, 0.505] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.124 [0.029, 0.257] | 0.667 [0.533, 0.790] | 0.514 [0.362, 0.667] | 0.543 [0.390, 0.695] | 0.171 [0.067, 0.286] | 0.476 [0.352, 0.600] | 0.000 [0.000, 0.000] | 0.514 [0.362, 0.667] | E1:0, E2:4, E3:0, E4:50, E5:0 |
| 2 | 105 | 0.105 [0.029, 0.210] | 0.610 [0.476, 0.733] | 0.486 [0.324, 0.657] | 0.505 [0.324, 0.686] | 0.143 [0.000, 0.276] | 0.448 [0.305, 0.590] | 0.000 [0.000, 0.000] | 0.486 [0.324, 0.657] | E1:0, E2:4, E3:0, E4:47, E5:0 |

## Heal loop, candidate policy per round

Mean with 95% bootstrap interval over seeds and tasks. Round 0 is the starting policy.

### filter_oracle: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.371 [0.257, 0.505] | 0.000 [0.000, 0.000] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.533 [0.390, 0.676] | 0.562 [0.438, 0.686] | 0.029 [0.000, 0.076] | 0.029 [0.000, 0.076] | 0.048 [0.000, 0.143] | 0.029 [0.000, 0.076] | 0.029 [0.000, 0.076] | 0.000 [0.000, 0.000] | E1:0, E2:0, E3:0, E4:2, E5:1 |
| 2 | 105 | 0.552 [0.429, 0.676] | 0.590 [0.486, 0.695] | 0.038 [0.000, 0.095] | 0.038 [0.000, 0.095] | 0.029 [0.000, 0.095] | 0.029 [0.000, 0.076] | 0.038 [0.000, 0.095] | 0.000 [0.000, 0.000] | E1:0, E2:1, E3:0, E4:1, E5:2 |

### filter_rule: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.114 [0.038, 0.210] | 0.638 [0.486, 0.790] | 0.505 [0.362, 0.657] | 0.524 [0.381, 0.676] | 0.124 [0.038, 0.238] | 0.505 [0.362, 0.657] | 0.124 [0.038, 0.238] | 0.505 [0.362, 0.657] | E1:0, E2:0, E3:0, E4:53, E5:0 |
| 2 | 105 | 0.181 [0.105, 0.276] | 0.629 [0.505, 0.762] | 0.419 [0.314, 0.533] | 0.448 [0.343, 0.562] | 0.038 [0.000, 0.124] | 0.419 [0.314, 0.533] | 0.038 [0.000, 0.124] | 0.419 [0.314, 0.533] | E1:0, E2:0, E3:0, E4:42, E5:2 |

### filter_sim: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.219 [0.143, 0.305] | 0.286 [0.181, 0.410] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.105 [0.038, 0.190] | 0.581 [0.457, 0.695] | 0.457 [0.352, 0.571] | 0.476 [0.371, 0.590] | 0.190 [0.095, 0.295] | 0.438 [0.343, 0.543] | 0.105 [0.038, 0.190] | 0.419 [0.333, 0.514] | E1:0, E2:2, E3:0, E4:46, E5:0 |
| 2 | 105 | 0.105 [0.010, 0.210] | 0.552 [0.457, 0.667] | 0.429 [0.324, 0.533] | 0.448 [0.333, 0.571] | 0.143 [0.029, 0.276] | 0.381 [0.276, 0.495] | 0.181 [0.105, 0.257] | 0.362 [0.248, 0.486] | E1:0, E2:5, E3:0, E4:40, E5:0 |

### iso_fix: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.181 [0.095, 0.267] | 0.667 [0.552, 0.771] | 0.467 [0.352, 0.581] | 0.486 [0.371, 0.600] | 0.048 [0.010, 0.095] | 0.467 [0.352, 0.581] | 0.048 [0.010, 0.095] | 0.467 [0.352, 0.581] | E1:0, E2:0, E3:0, E4:48, E5:1 |
| 2 | 105 | 0.581 [0.457, 0.724] | 0.590 [0.457, 0.733] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | 0.010 [0.000, 0.038] | E1:0, E2:0, E3:0, E4:0, E5:1 |

### iso_from_start: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.000 [0.000, 0.000] | 0.371 [0.257, 0.505] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.629 [0.495, 0.771] | 0.667 [0.524, 0.829] | 0.038 [0.000, 0.086] | 0.038 [0.000, 0.086] | 0.000 [0.000, 0.000] | 0.038 [0.000, 0.086] | 0.000 [0.000, 0.000] | 0.038 [0.000, 0.086] | E1:0, E2:0, E3:0, E4:0, E5:4 |
| 2 | 105 | 0.600 [0.486, 0.714] | 0.638 [0.533, 0.743] | 0.038 [0.000, 0.124] | 0.038 [0.000, 0.124] | 0.010 [0.000, 0.038] | 0.038 [0.000, 0.124] | 0.000 [0.000, 0.000] | 0.038 [0.000, 0.124] | E1:0, E2:0, E3:0, E4:0, E5:4 |

### weak_only: 3 seed(s) [0, 1, 2]

| round | n | true success | weak success | true hack rate H | false-pass rate | reported by D_rule | undetected by D_rule | reported by arm detector | U (arm detector) | exploit counts among hacks |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 105 | 0.076 [0.029, 0.133] | 0.476 [0.343, 0.619] | 0.371 [0.257, 0.505] | 0.400 [0.276, 0.524] | 0.286 [0.190, 0.381] | 0.286 [0.171, 0.410] | 0.000 [0.000, 0.000] | 0.371 [0.257, 0.505] | E1:0, E2:9, E3:0, E4:30, E5:0 |
| 1 | 105 | 0.124 [0.029, 0.257] | 0.667 [0.533, 0.790] | 0.514 [0.362, 0.667] | 0.543 [0.390, 0.695] | 0.171 [0.067, 0.286] | 0.476 [0.352, 0.600] | 0.000 [0.000, 0.000] | 0.514 [0.362, 0.667] | E1:0, E2:4, E3:0, E4:50, E5:0 |
| 2 | 105 | 0.152 [0.019, 0.286] | 0.552 [0.438, 0.676] | 0.390 [0.286, 0.505] | 0.400 [0.295, 0.524] | 0.143 [0.000, 0.305] | 0.390 [0.286, 0.505] | 0.000 [0.000, 0.000] | 0.390 [0.286, 0.505] | E1:0, E2:0, E3:0, E4:39, E5:2 |

## Paired comparisons

Difference with a paired 95% bootstrap interval over seeds and tasks. Deployed policies. Last round is round 2. With 3 seeds these are weak tests: read the intervals, not just the sign.

| comparison | metric | difference |
|---|---|---|
| filter_oracle: round 2 minus round 0 | undetected by D_rule | -0.257 [-0.429, -0.114] |
| filter_oracle: round 2 minus round 1 | undetected by D_rule | +0.000 [-0.057, +0.057] |
| filter_oracle: round 2 minus round 0 | reported by D_rule | -0.257 [-0.390, -0.133] |
| filter_oracle: round 2 minus round 1 | reported by D_rule | -0.019 [-0.076, +0.000] |
| filter_oracle: round 2 minus round 0 | true hack rate H | -0.333 [-0.524, -0.171] |
| filter_oracle: round 2 minus round 1 | true hack rate H | +0.010 [-0.057, +0.076] |
| filter_oracle: round 2 minus round 0 | true success | +0.476 [+0.295, +0.657] |
| filter_oracle: round 2 minus round 1 | true success | +0.019 [-0.124, +0.171] |
| filter_rule: round 2 minus round 0 | undetected by D_rule | +0.238 [+0.057, +0.486] |
| filter_rule: round 2 minus round 1 | undetected by D_rule | +0.019 [-0.029, +0.114] |
| filter_rule: round 2 minus round 0 | reported by D_rule | -0.190 [-0.324, -0.057] |
| filter_rule: round 2 minus round 1 | reported by D_rule | -0.029 [-0.114, +0.000] |
| filter_rule: round 2 minus round 0 | true hack rate H | +0.152 [-0.057, +0.429] |
| filter_rule: round 2 minus round 1 | true hack rate H | +0.019 [-0.029, +0.114] |
| filter_rule: round 2 minus round 0 | true success | +0.095 [-0.019, +0.229] |
| filter_rule: round 2 minus round 1 | true success | +0.057 [+0.000, +0.190] |
| filter_sim: round 2 minus round 0 | undetected by D_rule | +0.095 [-0.057, +0.267] |
| filter_sim: round 2 minus round 1 | undetected by D_rule | -0.029 [-0.171, +0.095] |
| filter_sim: round 2 minus round 0 | reported by D_rule | -0.152 [-0.324, +0.029] |
| filter_sim: round 2 minus round 1 | reported by D_rule | -0.086 [-0.305, +0.057] |
| filter_sim: round 2 minus round 0 | true hack rate H | +0.038 [-0.133, +0.229] |
| filter_sim: round 2 minus round 1 | true hack rate H | -0.048 [-0.171, +0.057] |
| filter_sim: round 2 minus round 0 | true success | +0.048 [-0.057, +0.171] |
| filter_sim: round 2 minus round 1 | true success | +0.048 [-0.038, +0.171] |
| iso_fix: round 2 minus round 0 | undetected by D_rule | -0.276 [-0.448, -0.114] |
| iso_fix: round 2 minus round 1 | undetected by D_rule | -0.457 [-0.629, -0.305] |
| iso_fix: round 2 minus round 0 | reported by D_rule | -0.276 [-0.410, -0.143] |
| iso_fix: round 2 minus round 1 | reported by D_rule | -0.038 [-0.095, +0.000] |
| iso_fix: round 2 minus round 0 | true hack rate H | -0.362 [-0.562, -0.181] |
| iso_fix: round 2 minus round 1 | true hack rate H | -0.457 [-0.629, -0.305] |
| iso_fix: round 2 minus round 0 | true success | +0.505 [+0.295, +0.705] |
| iso_fix: round 2 minus round 1 | true success | +0.400 [+0.181, +0.619] |
| iso_from_start: round 2 minus round 0 | undetected by D_rule | -0.229 [-0.429, -0.048] |
| iso_from_start: round 2 minus round 1 | undetected by D_rule | +0.019 [+0.000, +0.076] |
| iso_from_start: round 2 minus round 0 | reported by D_rule | -0.286 [-0.429, -0.143] |
| iso_from_start: round 2 minus round 1 | reported by D_rule | +0.000 [+0.000, +0.000] |
| iso_from_start: round 2 minus round 0 | true hack rate H | -0.314 [-0.524, -0.124] |
| iso_from_start: round 2 minus round 1 | true hack rate H | +0.019 [+0.000, +0.076] |
| iso_from_start: round 2 minus round 0 | true success | +0.552 [+0.343, +0.752] |
| iso_from_start: round 2 minus round 1 | true success | +0.000 [-0.057, +0.057] |
| weak_only: round 2 minus round 0 | undetected by D_rule | +0.162 [-0.048, +0.410] |
| weak_only: round 2 minus round 1 | undetected by D_rule | -0.029 [-0.095, +0.000] |
| weak_only: round 2 minus round 0 | reported by D_rule | -0.143 [-0.352, +0.038] |
| weak_only: round 2 minus round 1 | reported by D_rule | -0.029 [-0.114, +0.000] |
| weak_only: round 2 minus round 0 | true hack rate H | +0.114 [-0.133, +0.400] |
| weak_only: round 2 minus round 1 | true hack rate H | -0.029 [-0.095, +0.000] |
| weak_only: round 2 minus round 0 | true success | +0.029 [-0.086, +0.152] |
| weak_only: round 2 minus round 1 | true success | -0.019 [-0.114, +0.057] |
| filter_rule minus filter_sim, round 2 | undetected by D_rule | +0.143 [+0.000, +0.314] |
| filter_rule minus filter_sim, round 2 | true hack rate H | +0.114 [+0.000, +0.286] |
| filter_rule minus filter_sim, round 2 | true success | +0.048 [-0.057, +0.152] |
| filter_rule minus weak_only, round 2 | undetected by D_rule | +0.076 [-0.010, +0.181] |
| filter_rule minus weak_only, round 2 | true hack rate H | +0.038 [-0.067, +0.162] |
| filter_rule minus weak_only, round 2 | true success | +0.067 [-0.057, +0.181] |
| iso_fix minus filter_rule, round 2 | undetected by D_rule | -0.514 [-0.695, -0.333] |
| iso_fix minus filter_rule, round 2 | true hack rate H | -0.514 [-0.695, -0.333] |
| iso_fix minus filter_rule, round 2 | true success | +0.410 [+0.162, +0.657] |
| iso_fix minus weak_only, round 2 | undetected by D_rule | -0.438 [-0.629, -0.257] |
| iso_fix minus weak_only, round 2 | true hack rate H | -0.476 [-0.686, -0.267] |
| iso_fix minus weak_only, round 2 | true success | +0.476 [+0.229, +0.714] |
| iso_from_start minus weak_only, round 2 | undetected by D_rule | -0.390 [-0.610, -0.181] |
| iso_from_start minus weak_only, round 2 | true hack rate H | -0.429 [-0.676, -0.200] |
| iso_from_start minus weak_only, round 2 | true success | +0.524 [+0.295, +0.743] |
| filter_oracle minus filter_rule, round 2 | undetected by D_rule | -0.495 [-0.705, -0.295] |
| filter_oracle minus filter_rule, round 2 | true hack rate H | -0.486 [-0.695, -0.267] |
| filter_oracle minus filter_rule, round 2 | true success | +0.381 [+0.133, +0.619] |

### Pre-specified test for H1 (spec section 8), on candidates

Round 2 candidate minus round 1 candidate, so the effect of round 2 training is not hidden by gate rejections. When the gate rejected the round 2 candidate, the deployed table repeats round 1 for that seed.

| arm | metric | difference |
|---|---|---|
| filter_oracle | undetected by D_rule | +0.000 [-0.057, +0.057] |
| filter_oracle | reported by D_rule | -0.019 [-0.076, +0.000] |
| filter_oracle | true hack rate H | +0.010 [-0.057, +0.076] |
| filter_oracle | true success | +0.019 [-0.124, +0.171] |
| filter_rule | undetected by D_rule | -0.086 [-0.295, +0.105] |
| filter_rule | reported by D_rule | -0.086 [-0.267, +0.057] |
| filter_rule | true hack rate H | -0.086 [-0.295, +0.105] |
| filter_rule | true success | +0.067 [-0.095, +0.219] |
| filter_sim | undetected by D_rule | -0.057 [-0.190, +0.029] |
| filter_sim | reported by D_rule | -0.048 [-0.229, +0.095] |
| filter_sim | true hack rate H | -0.029 [-0.171, +0.086] |
| filter_sim | true success | +0.000 [-0.133, +0.143] |
| iso_fix | undetected by D_rule | -0.457 [-0.629, -0.305] |
| iso_fix | reported by D_rule | -0.038 [-0.095, +0.000] |
| iso_fix | true hack rate H | -0.457 [-0.629, -0.305] |
| iso_fix | true success | +0.400 [+0.181, +0.619] |
| iso_from_start | undetected by D_rule | +0.000 [-0.076, +0.076] |
| iso_from_start | reported by D_rule | +0.010 [+0.000, +0.057] |
| iso_from_start | true hack rate H | +0.000 [-0.076, +0.076] |
| iso_from_start | true success | -0.029 [-0.143, +0.086] |
| weak_only | undetected by D_rule | -0.086 [-0.190, +0.000] |
| weak_only | reported by D_rule | -0.029 [-0.143, +0.095] |
| weak_only | true hack rate H | -0.124 [-0.257, +0.000] |
| weak_only | true success | +0.029 [-0.124, +0.200] |

### Does the detector make the report cleaner than no detector?

| comparison | metric | difference |
|---|---|---|
| filter_rule minus weak_only, round 2 | reported by D_rule | -0.048 [-0.267, +0.229] |

### Noise floor: two arms that are identical through round 1

`iso_fix` and `filter_rule` have the same config, seed, starting adapter and curated data in round 1. Their round 1 candidates differ only by training and sampling nondeterminism. Any arm difference of this size is noise.

| comparison | metric | difference |
|---|---|---|
| iso_fix minus filter_rule, round 1 candidates | undetected by D_rule | -0.038 [-0.143, +0.048] |
| iso_fix minus filter_rule, round 1 candidates | reported by D_rule | -0.076 [-0.210, +0.029] |
| iso_fix minus filter_rule, round 1 candidates | true hack rate H | -0.038 [-0.143, +0.048] |
| iso_fix minus filter_rule, round 1 candidates | true success | +0.067 [-0.086, +0.210] |

## Loop internals per run

| arm | seed | round | signal | collected | kept as positives | flagged | failure types | gate: candidate vs deployed signal success | decision |
|---|---|---|---|---|---|---|---|---|---|
| filter_oracle | 0 | 1 | weak | 40 | 4 | 23 | {'pass': 4, 'cheat_flagged': 23, 'no_submit': 1, 'sql_error': 7, 'wrong_result': 5} | 0.33 vs 0.17 | deploy |
| filter_oracle | 0 | 2 | weak | 40 | 34 | 2 | {'pass': 34, 'cheat_flagged': 2, 'no_submit': 0, 'sql_error': 4, 'wrong_result': 0} | 0.33 vs 0.25 | deploy |
| filter_oracle | 1 | 1 | weak | 40 | 6 | 20 | {'pass': 6, 'cheat_flagged': 20, 'no_submit': 0, 'sql_error': 5, 'wrong_result': 9} | 0.50 vs 0.33 | deploy |
| filter_oracle | 1 | 2 | weak | 40 | 33 | 1 | {'pass': 33, 'cheat_flagged': 1, 'no_submit': 0, 'sql_error': 5, 'wrong_result': 1} | 0.67 vs 0.58 | deploy |
| filter_oracle | 2 | 1 | weak | 40 | 9 | 19 | {'pass': 9, 'cheat_flagged': 19, 'no_submit': 1, 'sql_error': 3, 'wrong_result': 8} | 0.25 vs 0.17 | deploy |
| filter_oracle | 2 | 2 | weak | 40 | 29 | 7 | {'pass': 29, 'cheat_flagged': 7, 'no_submit': 0, 'sql_error': 3, 'wrong_result': 1} | 0.33 vs 0.08 | deploy |
| filter_rule | 0 | 1 | weak | 40 | 24 | 5 | {'pass': 24, 'cheat_flagged': 5, 'no_submit': 1, 'sql_error': 6, 'wrong_result': 4} | 0.42 vs 0.17 | deploy |
| filter_rule | 0 | 2 | weak | 40 | 31 | 0 | {'pass': 31, 'cheat_flagged': 0, 'no_submit': 1, 'sql_error': 4, 'wrong_result': 4} | 0.67 vs 0.33 | deploy |
| filter_rule | 1 | 1 | weak | 40 | 22 | 13 | {'pass': 22, 'cheat_flagged': 13, 'no_submit': 0, 'sql_error': 2, 'wrong_result': 3} | 0.58 vs 0.33 | deploy |
| filter_rule | 1 | 2 | weak | 40 | 30 | 1 | {'pass': 30, 'cheat_flagged': 1, 'no_submit': 0, 'sql_error': 7, 'wrong_result': 2} | 0.25 vs 0.58 | reject |
| filter_rule | 2 | 1 | weak | 40 | 26 | 5 | {'pass': 26, 'cheat_flagged': 5, 'no_submit': 1, 'sql_error': 1, 'wrong_result': 7} | 0.33 vs 0.17 | deploy |
| filter_rule | 2 | 2 | weak | 40 | 30 | 1 | {'pass': 30, 'cheat_flagged': 1, 'no_submit': 1, 'sql_error': 5, 'wrong_result': 3} | 0.17 vs 0.42 | reject |
| filter_sim | 0 | 1 | weak | 40 | 23 | 6 | {'pass': 23, 'cheat_flagged': 6, 'no_submit': 1, 'sql_error': 6, 'wrong_result': 4} | 0.33 vs 0.17 | deploy |
| filter_sim | 0 | 2 | weak | 40 | 27 | 4 | {'pass': 27, 'cheat_flagged': 4, 'no_submit': 1, 'sql_error': 5, 'wrong_result': 3} | 0.33 vs 0.33 | deploy |
| filter_sim | 1 | 1 | weak | 40 | 20 | 9 | {'pass': 20, 'cheat_flagged': 9, 'no_submit': 0, 'sql_error': 3, 'wrong_result': 8} | 0.42 vs 0.33 | deploy |
| filter_sim | 1 | 2 | weak | 40 | 26 | 9 | {'pass': 26, 'cheat_flagged': 9, 'no_submit': 0, 'sql_error': 3, 'wrong_result': 2} | 0.25 vs 0.33 | reject |
| filter_sim | 2 | 1 | weak | 40 | 26 | 7 | {'pass': 26, 'cheat_flagged': 7, 'no_submit': 1, 'sql_error': 2, 'wrong_result': 4} | 0.33 vs 0.17 | reject |
| filter_sim | 2 | 2 | weak | 40 | 20 | 6 | {'pass': 20, 'cheat_flagged': 6, 'no_submit': 1, 'sql_error': 8, 'wrong_result': 5} | 0.50 vs 0.17 | deploy |
| iso_fix | 0 | 1 | weak | 40 | 24 | 5 | {'pass': 24, 'cheat_flagged': 5, 'no_submit': 1, 'sql_error': 6, 'wrong_result': 4} | 0.17 vs 0.17 | deploy |
| iso_fix | 0 | 2 | iso | 40 | 4 | 0 | {'pass': 4, 'cheat_flagged': 0, 'no_submit': 2, 'sql_error': 6, 'wrong_result': 28} | 0.33 vs 0.08 | deploy |
| iso_fix | 1 | 1 | weak | 40 | 22 | 13 | {'pass': 22, 'cheat_flagged': 13, 'no_submit': 0, 'sql_error': 2, 'wrong_result': 3} | 0.58 vs 0.33 | deploy |
| iso_fix | 1 | 2 | iso | 40 | 9 | 0 | {'pass': 9, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 7, 'wrong_result': 24} | 0.42 vs 0.08 | deploy |
| iso_fix | 2 | 1 | weak | 40 | 26 | 5 | {'pass': 26, 'cheat_flagged': 5, 'no_submit': 1, 'sql_error': 1, 'wrong_result': 7} | 0.33 vs 0.17 | deploy |
| iso_fix | 2 | 2 | iso | 40 | 12 | 0 | {'pass': 12, 'cheat_flagged': 0, 'no_submit': 3, 'sql_error': 3, 'wrong_result': 22} | 0.33 vs 0.25 | deploy |
| iso_from_start | 0 | 1 | iso | 40 | 4 | 0 | {'pass': 4, 'cheat_flagged': 0, 'no_submit': 1, 'sql_error': 7, 'wrong_result': 28} | 0.25 vs 0.00 | deploy |
| iso_from_start | 0 | 2 | iso | 40 | 33 | 0 | {'pass': 33, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 5, 'wrong_result': 2} | 0.33 vs 0.33 | deploy |
| iso_from_start | 1 | 1 | iso | 40 | 7 | 0 | {'pass': 7, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 5, 'wrong_result': 28} | 0.50 vs 0.00 | deploy |
| iso_from_start | 1 | 2 | iso | 40 | 34 | 0 | {'pass': 34, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 2, 'wrong_result': 4} | 0.42 vs 0.58 | reject |
| iso_from_start | 2 | 1 | iso | 40 | 8 | 0 | {'pass': 8, 'cheat_flagged': 0, 'no_submit': 1, 'sql_error': 3, 'wrong_result': 28} | 0.25 vs 0.00 | deploy |
| iso_from_start | 2 | 2 | iso | 40 | 31 | 0 | {'pass': 31, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 6, 'wrong_result': 3} | 0.33 vs 0.42 | reject |
| weak_only | 0 | 1 | weak | 40 | 27 | 0 | {'pass': 27, 'cheat_flagged': 0, 'no_submit': 1, 'sql_error': 7, 'wrong_result': 5} | 0.50 vs 0.17 | deploy |
| weak_only | 0 | 2 | weak | 40 | 30 | 0 | {'pass': 30, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 7, 'wrong_result': 3} | 0.42 vs 0.58 | reject |
| weak_only | 1 | 1 | weak | 40 | 26 | 0 | {'pass': 26, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 5, 'wrong_result': 9} | 0.33 vs 0.33 | deploy |
| weak_only | 1 | 2 | weak | 40 | 31 | 0 | {'pass': 31, 'cheat_flagged': 0, 'no_submit': 2, 'sql_error': 6, 'wrong_result': 1} | 0.17 vs 0.33 | reject |
| weak_only | 2 | 1 | weak | 40 | 28 | 0 | {'pass': 28, 'cheat_flagged': 0, 'no_submit': 1, 'sql_error': 3, 'wrong_result': 8} | 0.33 vs 0.17 | deploy |
| weak_only | 2 | 2 | weak | 40 | 31 | 0 | {'pass': 31, 'cheat_flagged': 0, 'no_submit': 0, 'sql_error': 2, 'wrong_result': 7} | 0.42 vs 0.42 | deploy |
