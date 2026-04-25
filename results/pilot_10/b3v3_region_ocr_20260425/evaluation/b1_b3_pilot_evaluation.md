# B1/B3/B3V2/B3V3 Pilot Evaluation

Reference: CIFP-derived canonical proxy JSON under `E:/experiment2/B1-B3/targets/canonical_proxy_gt_10`.

Numeric courses/radials are compared with +/-0.51 tolerance to avoid punishing display rounding such as 063 vs 063.3.

## Summary

| Method | Coverage | LegCountAcc | QFieldAcc | ChartExact | ExtraPredLegs | MissingPredLegs |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 1.000 | 0.500 | 0.495 | 0.000 | 2 | 4 |
| B3 | 1.000 | 0.200 | 0.344 | 0.000 | 1 | 7 |
| B3V2 | 1.000 | 0.800 | 0.484 | 0.000 | 1 | 1 |
| B3V3 | 1.000 | 0.900 | 0.887 | 0.200 | 2 | 0 |

## Per-Q Accuracy

| Method | Q_terminator | Q1_fix_ident | Q2_altitude_constraint | Q3_turn | Q4_course_or_radial | Q5_hold_params |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 0.484 | 0.710 | 0.355 | 0.516 | 0.355 | 0.548 |
| B3 | 0.258 | 0.548 | 0.290 | 0.323 | 0.161 | 0.484 |
| B3V2 | 0.581 | 0.903 | 0.323 | 0.161 | 0.290 | 0.645 |
| B3V3 | 0.968 | 0.968 | 0.871 | 0.935 | 0.742 | 0.839 |

## Per-Sample

### B1

| Chart | Output | LegCountExact | QMatch | QTotal | QAccuracy |
|---|---:|---:|---:|---:|---:|
| KABE_I06 | True | True | 10 | 18 | 0.556 |
| KACT_R32 | True | False | 4 | 18 | 0.222 |
| KALS_I02 | True | True | 17 | 18 | 0.944 |
| KAPC_I01L | True | False | 8 | 24 | 0.333 |
| KAQW_RNV-B | True | True | 9 | 18 | 0.500 |
| KATL_I09R | True | True | 12 | 18 | 0.667 |
| KBOS_L15R | True | False | 1 | 6 | 0.167 |
| KBOS_R32 | True | False | 11 | 24 | 0.458 |
| KCOE_L06 | True | True | 16 | 24 | 0.667 |
| KCOE_R02 | True | False | 4 | 18 | 0.222 |

### B3

| Chart | Output | LegCountExact | QMatch | QTotal | QAccuracy |
|---|---:|---:|---:|---:|---:|
| KABE_I06 | True | False | 6 | 18 | 0.333 |
| KACT_R32 | True | False | 3 | 18 | 0.167 |
| KALS_I02 | True | True | 13 | 18 | 0.722 |
| KAPC_I01L | True | False | 7 | 24 | 0.292 |
| KAQW_RNV-B | True | False | 2 | 18 | 0.111 |
| KATL_I09R | True | False | 7 | 18 | 0.389 |
| KBOS_L15R | True | False | 3 | 6 | 0.500 |
| KBOS_R32 | True | False | 4 | 24 | 0.167 |
| KCOE_L06 | True | True | 16 | 24 | 0.667 |
| KCOE_R02 | True | False | 3 | 18 | 0.167 |

### B3V2

| Chart | Output | LegCountExact | QMatch | QTotal | QAccuracy |
|---|---:|---:|---:|---:|---:|
| KABE_I06 | True | True | 8 | 18 | 0.444 |
| KACT_R32 | True | True | 10 | 18 | 0.556 |
| KALS_I02 | True | True | 13 | 18 | 0.722 |
| KAPC_I01L | True | True | 12 | 24 | 0.500 |
| KAQW_RNV-B | True | False | 2 | 18 | 0.111 |
| KATL_I09R | True | True | 8 | 18 | 0.444 |
| KBOS_L15R | True | False | 3 | 6 | 0.500 |
| KBOS_R32 | True | True | 11 | 24 | 0.458 |
| KCOE_L06 | True | True | 15 | 24 | 0.625 |
| KCOE_R02 | True | True | 8 | 18 | 0.444 |

### B3V3

| Chart | Output | LegCountExact | QMatch | QTotal | QAccuracy |
|---|---:|---:|---:|---:|---:|
| KABE_I06 | True | True | 18 | 18 | 1.000 |
| KACT_R32 | True | True | 15 | 18 | 0.833 |
| KALS_I02 | True | True | 15 | 18 | 0.833 |
| KAPC_I01L | True | True | 22 | 24 | 0.917 |
| KAQW_RNV-B | True | True | 15 | 18 | 0.833 |
| KATL_I09R | True | True | 18 | 18 | 1.000 |
| KBOS_L15R | True | False | 2 | 6 | 0.333 |
| KBOS_R32 | True | True | 22 | 24 | 0.917 |
| KCOE_L06 | True | True | 23 | 24 | 0.958 |
| KCOE_R02 | True | True | 15 | 18 | 0.833 |
