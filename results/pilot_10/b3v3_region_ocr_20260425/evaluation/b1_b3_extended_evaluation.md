# B1/B3 Extended Pilot Evaluation

Reference target: `E:/experiment2/B1-B3/targets/canonical_proxy_gt_10`.

The scorer uses indexed-leg alignment and the PR #28 canonical Q-field schema.

## Exact Extraction Metrics

| Method | Coverage | QFieldAcc | Precision | Recall | F1 | ChartExact | ExtraLegs | MissingLegs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B1 | 1.000 | 0.495 | 0.560 | 0.451 | 0.500 | 0.000 | 2 | 4 |
| B3 | 1.000 | 0.344 | 0.422 | 0.310 | 0.357 | 0.000 | 1 | 7 |
| B3V2 | 1.000 | 0.484 | 0.621 | 0.522 | 0.567 | 0.000 | 1 | 1 |
| B3V3 | 1.000 | 0.887 | 0.949 | 0.823 | 0.882 | 0.200 | 2 | 0 |

## Error Breakdown

| Method | WrongValue | FalsePositive | FalseNegative | NonPresentStatusMismatch | OverRate | UnderRate |
|---|---:|---:|---:|---:|---:|---:|
| B1 | 30 | 10 | 32 | 22 | 0.054 | 0.172 |
| B3 | 32 | 16 | 46 | 28 | 0.086 | 0.247 |
| B3V2 | 26 | 10 | 28 | 32 | 0.054 | 0.151 |
| B3V3 | 5 | 0 | 15 | 1 | 0.000 | 0.081 |

## Relation Labels

| Method | Supported | Partial | NotObservable | Contradicted |
|---|---:|---:|---:|---:|
| B1 | 0.495 | 0.145 | 0.167 | 0.194 |
| B3 | 0.344 | 0.129 | 0.301 | 0.226 |
| B3V2 | 0.484 | 0.242 | 0.151 | 0.124 |
| B3V3 | 0.887 | 0.027 | 0.048 | 0.038 |

## Bootstrap 95% CI

| Method | QFieldAcc CI | LegCountAcc CI | ChartExact CI |
|---|---:|---:|---:|
| B1 | 0.495 [0.362, 0.630] | 0.500 [0.200, 0.800] | 0.000 [0.000, 0.000] |
| B3 | 0.344 [0.217, 0.485] | 0.200 [0.000, 0.500] | 0.000 [0.000, 0.000] |
| B3V2 | 0.484 [0.382, 0.570] | 0.800 [0.500, 1.000] | 0.000 [0.000, 0.000] |
| B3V3 | 0.887 [0.827, 0.935] | 0.900 [0.700, 1.000] | 0.200 [0.000, 0.500] |

## Weakest Fields By Method

### B1

| Q Field | ExactAcc | Precision | Recall | FP | FN | WrongValue |
|---|---:|---:|---:|---:|---:|---:|
| Q2_altitude_constraint | 0.355 | 0.556 | 0.370 | 2 | 11 | 6 |
| Q4_course_or_radial | 0.355 | 0.600 | 0.474 | 1 | 5 | 5 |
| Q_terminator | 0.484 | 0.556 | 0.484 | 0 | 4 | 12 |
| Q3_turn | 0.516 | 0.500 | 0.500 | 1 | 1 | 1 |
| Q5_hold_params | 0.548 | 0.000 | 0.000 | 4 | 5 | 5 |
| Q1_fix_ident | 0.710 | 0.833 | 0.682 | 2 | 6 | 1 |

### B3

| Q Field | ExactAcc | Precision | Recall | FP | FN | WrongValue |
|---|---:|---:|---:|---:|---:|---:|
| Q4_course_or_radial | 0.161 | 0.417 | 0.263 | 1 | 8 | 6 |
| Q_terminator | 0.258 | 0.333 | 0.258 | 0 | 7 | 16 |
| Q2_altitude_constraint | 0.290 | 0.500 | 0.333 | 3 | 12 | 6 |
| Q3_turn | 0.323 | 0.333 | 0.250 | 2 | 3 | 0 |
| Q5_hold_params | 0.484 | 0.000 | 0.000 | 6 | 8 | 2 |
| Q1_fix_ident | 0.548 | 0.667 | 0.545 | 4 | 8 | 2 |

### B3V2

| Q Field | ExactAcc | Precision | Recall | FP | FN | WrongValue |
|---|---:|---:|---:|---:|---:|---:|
| Q3_turn | 0.161 | 0.500 | 0.500 | 2 | 2 | 0 |
| Q4_course_or_radial | 0.290 | 0.600 | 0.474 | 3 | 7 | 3 |
| Q2_altitude_constraint | 0.323 | 0.556 | 0.370 | 3 | 12 | 5 |
| Q_terminator | 0.581 | 0.643 | 0.581 | 0 | 3 | 10 |
| Q5_hold_params | 0.645 | 0.000 | 0.000 | 1 | 2 | 8 |
| Q1_fix_ident | 0.903 | 0.952 | 0.909 | 1 | 2 | 0 |

### B3V3

| Q Field | ExactAcc | Precision | Recall | FP | FN | WrongValue |
|---|---:|---:|---:|---:|---:|---:|
| Q4_course_or_radial | 0.742 | 1.000 | 0.632 | 0 | 7 | 0 |
| Q5_hold_params | 0.839 | 0.556 | 0.500 | 0 | 1 | 4 |
| Q2_altitude_constraint | 0.871 | 1.000 | 0.852 | 0 | 4 | 0 |
| Q3_turn | 0.935 | 1.000 | 0.500 | 0 | 2 | 0 |
| Q_terminator | 0.968 | 0.968 | 0.968 | 0 | 0 | 1 |
| Q1_fix_ident | 0.968 | 1.000 | 0.955 | 0 | 1 | 0 |
