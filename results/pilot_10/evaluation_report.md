# Experiment Evaluation Report

Reference baseline: Path O

## Summary

| Path | OutputCoverage | ScalarPrecision | ScalarRecall | ScalarF1 | WaypointPrecision | WaypointRecall | WaypointF1 | MeanWaypointJaccard | WaypointExactRate |
|------|----------------|-----------------|--------------|----------|-------------------|----------------|------------|---------------------|-------------------|
| A | 1.000 | 0.786 | 0.550 | 0.647 | 0.200 | 0.583 | 0.298 | 0.159 | 0.000 |
| B | 1.000 | 0.875 | 0.875 | 0.875 | 0.917 | 0.917 | 0.917 | 0.900 | 0.900 |
| C | 1.000 | 0.975 | 0.975 | 0.975 | 0.917 | 0.917 | 0.917 | 0.900 | 0.900 |
| D | 1.000 | 0.950 | 0.950 | 0.950 | 0.917 | 0.917 | 0.917 | 0.900 | 0.900 |

## Field Details

### Path A

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 7 | 1 | 3 | 0.875 | 0.700 | 0.778 |
| turn_direction | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| holding_required | 5 | 5 | 5 | 0.500 | 0.500 | 0.500 |
| holding_fix | 0 | 0 | 10 | N/A | 0.000 | N/A |
| waypoints | 7 | 28 | 5 | 0.200 | 0.583 | 0.298 |

### Path B

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| turn_direction | 6 | 4 | 4 | 0.600 | 0.600 | 0.600 |
| holding_required | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| holding_fix | 9 | 1 | 1 | 0.900 | 0.900 | 0.900 |
| waypoints | 11 | 1 | 1 | 0.917 | 0.917 | 0.917 |

### Path C

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| turn_direction | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| holding_required | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| holding_fix | 9 | 1 | 1 | 0.900 | 0.900 | 0.900 |
| waypoints | 11 | 1 | 1 | 0.917 | 0.917 | 0.917 |

### Path D

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 9 | 1 | 1 | 0.900 | 0.900 | 0.900 |
| turn_direction | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| holding_required | 10 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| holding_fix | 9 | 1 | 1 | 0.900 | 0.900 | 0.900 |
| waypoints | 11 | 1 | 1 | 0.917 | 0.917 | 0.917 |

## Per-Sample Snapshot

### Path A

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KAAT_R31 | True | 0.750 | False | 0.200 |
| KABE_R06 | True | 0.250 | False | 0.000 |
| KABE_R13 | True | 0.750 | False | 0.222 |
| KABE_R24 | True | 0.500 | False | 0.500 |
| KABE_R31 | True | 0.250 | False | 0.000 |
| KABI_I35R | True | 0.500 | False | 0.000 |
| KAAA_R03 | True | 0.750 | False | 0.250 |
| KAAA_R21 | True | 0.750 | False | 0.250 |
| KAAF_R06 | True | 0.750 | False | 0.167 |
| KAAF_R14 | True | 0.250 | False | 0.000 |

### Path B

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KAAT_R31 | True | 1.000 | True | 1.000 |
| KABE_R06 | True | 0.750 | True | 1.000 |
| KABE_R13 | True | 0.750 | True | 1.000 |
| KABE_R24 | True | 0.750 | True | 1.000 |
| KABE_R31 | True | 0.750 | True | 1.000 |
| KABI_I35R | True | 0.750 | False | 0.000 |
| KAAA_R03 | True | 1.000 | True | 1.000 |
| KAAA_R21 | True | 1.000 | True | 1.000 |
| KAAF_R06 | True | 1.000 | True | 1.000 |
| KAAF_R14 | True | 1.000 | True | 1.000 |

### Path C

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KAAT_R31 | True | 1.000 | True | 1.000 |
| KABE_R06 | True | 1.000 | True | 1.000 |
| KABE_R13 | True | 1.000 | True | 1.000 |
| KABE_R24 | True | 1.000 | True | 1.000 |
| KABE_R31 | True | 1.000 | True | 1.000 |
| KABI_I35R | True | 0.750 | False | 0.000 |
| KAAA_R03 | True | 1.000 | True | 1.000 |
| KAAA_R21 | True | 1.000 | True | 1.000 |
| KAAF_R06 | True | 1.000 | True | 1.000 |
| KAAF_R14 | True | 1.000 | True | 1.000 |

### Path D

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KAAT_R31 | True | 0.750 | True | 1.000 |
| KABE_R06 | True | 1.000 | True | 1.000 |
| KABE_R13 | True | 1.000 | True | 1.000 |
| KABE_R24 | True | 1.000 | True | 1.000 |
| KABE_R31 | True | 1.000 | True | 1.000 |
| KABI_I35R | True | 0.750 | False | 0.000 |
| KAAA_R03 | True | 1.000 | True | 1.000 |
| KAAA_R21 | True | 1.000 | True | 1.000 |
| KAAF_R06 | True | 1.000 | True | 1.000 |
| KAAF_R14 | True | 1.000 | True | 1.000 |
