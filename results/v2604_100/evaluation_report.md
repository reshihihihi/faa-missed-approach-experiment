# Experiment Evaluation Report

Reference baseline: Path O

## Summary

| Path | OutputCoverage | ScalarPrecision | ScalarRecall | ScalarF1 | WaypointPrecision | WaypointRecall | WaypointF1 | MeanWaypointJaccard | WaypointExactRate |
|------|----------------|-----------------|--------------|----------|-------------------|----------------|------------|---------------------|-------------------|
| A | 1.000 | 0.600 | 0.661 | 0.629 | 0.357 | 0.563 | 0.437 | 0.391 | 0.350 |
| B | 1.000 | 0.537 | 0.651 | 0.588 | 0.496 | 0.930 | 0.647 | 0.513 | 0.480 |
| C | 1.000 | 0.644 | 0.780 | 0.705 | 0.545 | 0.944 | 0.691 | 0.555 | 0.550 |
| D | 1.000 | 0.623 | 0.758 | 0.684 | 0.528 | 0.944 | 0.677 | 0.545 | 0.530 |
| E | 1.000 | 0.628 | 0.758 | 0.687 | 0.545 | 0.930 | 0.688 | 0.545 | 0.540 |

## Field Details

### Path A

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 53 | 36 | 12 | 0.596 | 0.815 | 0.688 |
| turn_direction | 70 | 30 | 30 | 0.700 | 0.700 | 0.700 |
| holding_required | 56 | 44 | 44 | 0.560 | 0.560 | 0.560 |
| holding_fix | 37 | 34 | 25 | 0.521 | 0.597 | 0.556 |
| waypoints | 40 | 72 | 31 | 0.357 | 0.563 | 0.437 |

### Path B

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 61 | 38 | 4 | 0.616 | 0.938 | 0.744 |
| turn_direction | 31 | 69 | 69 | 0.310 | 0.310 | 0.310 |
| holding_required | 64 | 36 | 36 | 0.640 | 0.640 | 0.640 |
| holding_fix | 57 | 41 | 5 | 0.582 | 0.919 | 0.712 |
| waypoints | 66 | 67 | 5 | 0.496 | 0.930 | 0.647 |

### Path C

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 65 | 35 | 0 | 0.650 | 1.000 | 0.788 |
| turn_direction | 68 | 32 | 32 | 0.680 | 0.680 | 0.680 |
| holding_required | 65 | 35 | 35 | 0.650 | 0.650 | 0.650 |
| holding_fix | 57 | 39 | 5 | 0.594 | 0.919 | 0.722 |
| waypoints | 67 | 56 | 4 | 0.545 | 0.944 | 0.691 |

### Path D

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 65 | 35 | 0 | 0.650 | 1.000 | 0.788 |
| turn_direction | 61 | 39 | 39 | 0.610 | 0.610 | 0.610 |
| holding_required | 64 | 36 | 36 | 0.640 | 0.640 | 0.640 |
| holding_fix | 58 | 40 | 4 | 0.592 | 0.935 | 0.725 |
| waypoints | 67 | 60 | 4 | 0.528 | 0.944 | 0.677 |

### Path E

| Field | TP | FP | FN | Precision | Recall | F1 |
|-------|----|----|----|-----------|--------|----|
| climb_altitude | 62 | 37 | 3 | 0.626 | 0.954 | 0.756 |
| turn_direction | 68 | 31 | 32 | 0.687 | 0.680 | 0.683 |
| holding_required | 62 | 37 | 38 | 0.626 | 0.620 | 0.623 |
| holding_fix | 56 | 42 | 6 | 0.571 | 0.903 | 0.700 |
| waypoints | 66 | 55 | 5 | 0.545 | 0.930 | 0.688 |

## Per-Sample Snapshot

### Path A

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KABE_I06 | True | 1.000 | False | 0.000 |
| KALS_I02 | True | 1.000 | False | 0.000 |
| KAMA_I04 | True | 0.000 | False | 0.000 |
| KAPC_I01L | True | 0.500 | False | 0.000 |
| KATL_I09R | True | 1.000 | False | 0.000 |
| KAUS_I18L | True | 0.500 | False | 0.000 |
| KAVL_I17 | True | 0.750 | True | 1.000 |
| KAYS_I19-Z | True | 0.500 | False | 0.000 |
| KBMI_I29 | True | 0.750 | False | 0.000 |
| KBUY_I06-Z | True | 1.000 | False | 0.000 |
| KBWG_I03-Y | True | 0.000 | False | 0.000 |
| KCFO_I26 | True | 0.750 | True | 1.000 |
| KCMH_I10R | True | 0.250 | False | 0.000 |
| KAVP_L04 | True | 0.000 | True | 1.000 |
| KAXH_L09 | True | 1.000 | True | 1.000 |
| KBDL_L33 | True | 0.000 | True | 1.000 |
| KBDR_L06 | True | 0.000 | False | 0.000 |
| KBFF_L12 | True | 0.500 | True | 1.000 |
| KBOS_L15R | True | 0.500 | False | 0.000 |
| KBUR_L08-Z | True | 0.500 | True | 1.000 |
| KBYL_L20 | True | 0.500 | True | 1.000 |
| KCEC_L12 | True | 1.000 | False | 0.000 |
| KCFO_L17 | True | 0.500 | False | 0.000 |
| KCOE_L06 | True | 0.000 | True | 1.000 |
| KCRP_L36 | True | 1.000 | True | 1.000 |
| KCRW_L05 | True | 0.500 | True | 1.000 |
| KALN_L29 | True | 0.500 | False | 0.500 |
| KALO_L12 | True | 0.750 | True | 1.000 |
| KAWM_L17 | True | 0.500 | False | 0.000 |
| KBPT_L12 | True | 0.000 | False | 0.000 |
| KBRD_L34 | True | 0.750 | False | 0.000 |
| KBTL_L23R | True | 0.750 | False | 0.000 |
| KBTP_L08 | True | 1.000 | False | 0.000 |
| KBWI_L15L | True | 0.750 | False | 0.000 |
| KCAK_L01 | True | 0.750 | False | 0.000 |
| KCBF_L36 | True | 0.750 | False | 0.000 |
| KCHA_L20 | True | 0.500 | False | 0.000 |
| KCJR_L04 | True | 0.750 | True | 1.000 |
| KAFN_RNV-B | True | 0.500 | False | 0.000 |
| KAFN_RNV-C | True | 0.500 | False | 0.000 |
| KAIB_RNV-A | True | 0.000 | False | 0.000 |
| KANP_RNV-A | True | 0.000 | False | 0.000 |
| KAPT_R04 | True | 0.500 | False | 0.000 |
| KAPV_R18 | True | 0.500 | False | 0.000 |
| KAQW_RNV-A | True | 0.000 | False | 0.000 |
| KAQW_RNV-B | True | 1.000 | False | 0.000 |
| KAVQ_R12 | True | 0.000 | False | 0.000 |
| KAVQ_R21 | True | 0.500 | False | 0.000 |
| KAXH_R27 | True | 1.000 | False | 0.667 |
| KBDH_R31 | True | 0.667 | False | 0.000 |
| KBDN_R34 | True | 0.500 | False | 0.000 |
| KBJC_R12L | True | 0.000 | False | 0.000 |
| KBLF_R05 | True | 0.000 | False | 0.000 |
| KBMQ_R01 | True | 0.500 | False | 0.000 |
| KBOS_R32 | True | 0.500 | False | 0.000 |
| KBTV_R33-Y | True | 0.500 | False | 0.000 |
| KBUR_R08-Z | True | 0.000 | False | 0.000 |
| KBWC_R26 | True | 0.500 | True | 1.000 |
| KCAG_R07 | True | 0.500 | True | 1.000 |
| KCBE_R05 | True | 1.000 | False | 0.000 |
| KCEA_RNV-D | True | 0.000 | False | 0.000 |
| KCII_R33 | True | 0.500 | False | 0.000 |
| KCOE_R02 | True | 0.500 | False | 0.000 |
| KACT_R32 | True | 1.000 | True | 1.000 |
| KADF_R22 | True | 1.000 | True | 1.000 |
| KAKH_R03 | True | 1.000 | False | 0.600 |
| KANY_R18 | True | 1.000 | True | 1.000 |
| KAOO_R03-Z | True | 1.000 | True | 1.000 |
| KAOO_R21 | True | 1.000 | True | 1.000 |
| KARG_R04 | True | 1.000 | False | 0.500 |
| KATW_R21 | True | 1.000 | True | 1.000 |
| KAVP_R22 | True | 1.000 | True | 1.000 |
| KAWG_R36 | True | 1.000 | True | 1.000 |
| KAXN_R22 | True | 0.750 | True | 1.000 |
| KAXV_R26 | True | 0.500 | False | 0.000 |
| KAZC_R29 | True | 0.000 | False | 0.000 |
| KBFD_R14 | True | 1.000 | False | 0.500 |
| KBJI_R31 | True | 0.500 | False | 0.000 |
| KBKW_R01 | True | 1.000 | True | 1.000 |
| KBKX_R30 | True | 1.000 | True | 1.000 |
| KBLV_R32RY | True | 0.250 | False | 0.000 |
| KBTR_R04L | True | 1.000 | True | 1.000 |
| KBUM_R18 | True | 0.750 | True | 1.000 |
| KBVY_R34 | True | 1.000 | True | 1.000 |
| KBXA_R18 | True | 1.000 | True | 1.000 |
| KBYH_R36 | True | 1.000 | True | 1.000 |
| KBYI_R20 | True | 1.000 | False | 0.333 |
| KCAO_R02 | True | 1.000 | True | 1.000 |
| KCBF_R36 | True | 1.000 | True | 1.000 |
| KCDI_R04 | True | 0.500 | False | 0.000 |
| KCDR_R03 | True | 0.250 | False | 0.000 |
| KCDS_R36 | True | 1.000 | False | 0.500 |
| KCGI_R10 | True | 0.500 | False | 0.000 |
| KCHO_R03 | True | 0.750 | False | 0.000 |
| KCHQ_R36 | True | 0.250 | False | 0.000 |
| KCIC_R13L | True | 0.750 | False | 0.000 |
| KCLL_R11 | True | 1.000 | True | 1.000 |
| KCNC_R10 | True | 1.000 | True | 1.000 |
| KCOI_R11 | True | 0.750 | False | 0.500 |
| KCRS_R32 | True | 0.000 | False | 0.000 |

### Path B

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KABE_I06 | True | 1.000 | False | 0.000 |
| KALS_I02 | True | 1.000 | True | 1.000 |
| KAMA_I04 | True | 0.750 | False | 0.500 |
| KAPC_I01L | True | 0.750 | True | 1.000 |
| KATL_I09R | True | 0.750 | False | 0.000 |
| KAUS_I18L | True | 0.750 | False | 0.500 |
| KAVL_I17 | True | 0.750 | False | 0.000 |
| KAYS_I19-Z | True | 0.500 | False | 0.000 |
| KBMI_I29 | True | 0.750 | True | 1.000 |
| KBUY_I06-Z | True | 1.000 | True | 1.000 |
| KBWG_I03-Y | True | 1.000 | True | 1.000 |
| KCFO_I26 | True | 0.750 | False | 0.500 |
| KCMH_I10R | True | 1.000 | True | 1.000 |
| KAVP_L04 | True | 0.000 | False | 0.000 |
| KAXH_L09 | True | 1.000 | True | 1.000 |
| KBDL_L33 | True | 0.000 | False | 0.000 |
| KBDR_L06 | True | 0.000 | False | 0.000 |
| KBFF_L12 | True | 0.000 | False | 0.000 |
| KBOS_L15R | True | 0.000 | False | 0.000 |
| KBUR_L08-Z | True | 0.000 | False | 0.000 |
| KBYL_L20 | True | 0.000 | False | 0.000 |
| KCEC_L12 | True | 0.000 | False | 0.000 |
| KCFO_L17 | True | 0.500 | False | 0.000 |
| KCOE_L06 | True | 0.000 | False | 0.000 |
| KCRP_L36 | True | 0.000 | False | 0.000 |
| KCRW_L05 | True | 0.000 | False | 0.000 |
| KALN_L29 | True | 0.500 | False | 0.333 |
| KALO_L12 | True | 0.750 | False | 0.500 |
| KAWM_L17 | True | 0.750 | True | 1.000 |
| KBPT_L12 | True | 1.000 | True | 1.000 |
| KBRD_L34 | True | 0.750 | False | 0.000 |
| KBTL_L23R | True | 0.750 | False | 0.000 |
| KBTP_L08 | True | 1.000 | True | 1.000 |
| KBWI_L15L | True | 1.000 | False | 0.000 |
| KCAK_L01 | True | 0.750 | True | 1.000 |
| KCBF_L36 | True | 1.000 | False | 0.500 |
| KCHA_L20 | True | 0.750 | True | 1.000 |
| KCJR_L04 | True | 0.750 | False | 0.500 |
| KAFN_RNV-B | True | 0.000 | False | 0.000 |
| KAFN_RNV-C | True | 0.500 | False | 0.000 |
| KAIB_RNV-A | True | 0.000 | False | 0.000 |
| KANP_RNV-A | True | 0.000 | False | 0.000 |
| KAPT_R04 | True | 0.000 | False | 0.000 |
| KAPV_R18 | True | 0.000 | False | 0.000 |
| KAQW_RNV-A | True | 0.000 | False | 0.000 |
| KAQW_RNV-B | True | 0.000 | False | 0.000 |
| KAVQ_R12 | True | 0.000 | False | 0.000 |
| KAVQ_R21 | True | 0.000 | False | 0.000 |
| KAXH_R27 | True | 0.667 | True | 1.000 |
| KBDH_R31 | True | 0.333 | False | 0.000 |
| KBDN_R34 | True | 0.000 | False | 0.000 |
| KBJC_R12L | True | 0.000 | False | 0.000 |
| KBLF_R05 | True | 0.000 | False | 0.000 |
| KBMQ_R01 | True | 0.000 | False | 0.000 |
| KBOS_R32 | True | 0.000 | False | 0.000 |
| KBTV_R33-Y | True | 0.000 | False | 0.000 |
| KBUR_R08-Z | True | 0.000 | False | 0.000 |
| KBWC_R26 | True | 0.000 | False | 0.000 |
| KCAG_R07 | True | 0.000 | False | 0.000 |
| KCBE_R05 | True | 0.000 | False | 0.000 |
| KCEA_RNV-D | True | 0.000 | False | 0.000 |
| KCII_R33 | True | 0.500 | False | 0.000 |
| KCOE_R02 | True | 0.500 | False | 0.000 |
| KACT_R32 | True | 0.750 | True | 1.000 |
| KADF_R22 | True | 1.000 | True | 1.000 |
| KAKH_R03 | True | 0.750 | True | 1.000 |
| KANY_R18 | True | 1.000 | True | 1.000 |
| KAOO_R03-Z | True | 0.750 | True | 1.000 |
| KAOO_R21 | True | 0.750 | True | 1.000 |
| KARG_R04 | True | 1.000 | True | 1.000 |
| KATW_R21 | True | 1.000 | True | 1.000 |
| KAVP_R22 | True | 1.000 | True | 1.000 |
| KAWG_R36 | True | 0.750 | True | 1.000 |
| KAXN_R22 | True | 0.750 | True | 1.000 |
| KAXV_R26 | True | 0.750 | True | 1.000 |
| KAZC_R29 | True | 0.750 | True | 1.000 |
| KBFD_R14 | True | 0.750 | True | 1.000 |
| KBJI_R31 | True | 0.750 | True | 1.000 |
| KBKW_R01 | True | 0.750 | True | 1.000 |
| KBKX_R30 | True | 1.000 | True | 1.000 |
| KBLV_R32RY | True | 0.500 | False | 0.000 |
| KBTR_R04L | True | 0.750 | True | 1.000 |
| KBUM_R18 | True | 0.750 | True | 1.000 |
| KBVY_R34 | True | 0.750 | True | 1.000 |
| KBXA_R18 | True | 1.000 | True | 1.000 |
| KBYH_R36 | True | 1.000 | True | 1.000 |
| KBYI_R20 | True | 1.000 | True | 1.000 |
| KCAO_R02 | True | 0.750 | True | 1.000 |
| KCBF_R36 | True | 0.750 | True | 1.000 |
| KCDI_R04 | True | 0.750 | True | 1.000 |
| KCDR_R03 | True | 0.750 | True | 1.000 |
| KCDS_R36 | True | 1.000 | True | 1.000 |
| KCGI_R10 | True | 0.750 | True | 1.000 |
| KCHO_R03 | True | 1.000 | True | 1.000 |
| KCHQ_R36 | True | 0.750 | True | 1.000 |
| KCIC_R13L | True | 0.500 | False | 0.000 |
| KCLL_R11 | True | 0.750 | True | 1.000 |
| KCNC_R10 | True | 0.750 | True | 1.000 |
| KCOI_R11 | True | 0.750 | True | 1.000 |
| KCRS_R32 | True | 1.000 | True | 1.000 |

### Path C

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KABE_I06 | True | 1.000 | False | 0.000 |
| KALS_I02 | True | 1.000 | True | 1.000 |
| KAMA_I04 | True | 0.750 | True | 1.000 |
| KAPC_I01L | True | 1.000 | True | 1.000 |
| KATL_I09R | True | 1.000 | False | 0.000 |
| KAUS_I18L | True | 0.750 | True | 1.000 |
| KAVL_I17 | True | 1.000 | False | 0.000 |
| KAYS_I19-Z | True | 0.750 | False | 0.000 |
| KBMI_I29 | True | 0.750 | True | 1.000 |
| KBUY_I06-Z | True | 1.000 | True | 1.000 |
| KBWG_I03-Y | True | 1.000 | True | 1.000 |
| KCFO_I26 | True | 0.750 | False | 0.500 |
| KCMH_I10R | True | 0.750 | True | 1.000 |
| KAVP_L04 | True | 0.000 | False | 0.000 |
| KAXH_L09 | True | 1.000 | True | 1.000 |
| KBDL_L33 | True | 0.000 | False | 0.000 |
| KBDR_L06 | True | 0.000 | False | 0.000 |
| KBFF_L12 | True | 0.000 | False | 0.000 |
| KBOS_L15R | True | 0.500 | False | 0.000 |
| KBUR_L08-Z | True | 0.000 | False | 0.000 |
| KBYL_L20 | True | 0.000 | False | 0.000 |
| KCEC_L12 | True | 0.000 | False | 0.000 |
| KCFO_L17 | True | 0.500 | False | 0.000 |
| KCOE_L06 | True | 0.000 | False | 0.000 |
| KCRP_L36 | True | 0.000 | False | 0.000 |
| KCRW_L05 | True | 0.000 | False | 0.000 |
| KALN_L29 | True | 0.750 | False | 0.000 |
| KALO_L12 | True | 0.750 | True | 1.000 |
| KAWM_L17 | True | 0.750 | True | 1.000 |
| KBPT_L12 | True | 1.000 | True | 1.000 |
| KBRD_L34 | True | 0.750 | False | 0.000 |
| KBTL_L23R | True | 1.000 | True | 1.000 |
| KBTP_L08 | True | 1.000 | True | 1.000 |
| KBWI_L15L | True | 1.000 | False | 0.000 |
| KCAK_L01 | True | 0.750 | True | 1.000 |
| KCBF_L36 | True | 1.000 | True | 1.000 |
| KCHA_L20 | True | 1.000 | True | 1.000 |
| KCJR_L04 | True | 0.750 | True | 1.000 |
| KAFN_RNV-B | True | 0.500 | False | 0.000 |
| KAFN_RNV-C | True | 0.500 | False | 0.000 |
| KAIB_RNV-A | True | 0.000 | False | 0.000 |
| KANP_RNV-A | True | 0.000 | False | 0.000 |
| KAPT_R04 | True | 0.500 | False | 0.000 |
| KAPV_R18 | True | 0.500 | False | 0.000 |
| KAQW_RNV-A | True | 0.000 | False | 0.000 |
| KAQW_RNV-B | True | 0.000 | False | 0.000 |
| KAVQ_R12 | True | 0.000 | False | 0.000 |
| KAVQ_R21 | True | 0.500 | False | 0.000 |
| KAXH_R27 | True | 1.000 | True | 1.000 |
| KBDH_R31 | True | 0.667 | False | 0.000 |
| KBDN_R34 | True | 0.500 | False | 0.000 |
| KBJC_R12L | True | 0.000 | False | 0.000 |
| KBLF_R05 | True | 0.000 | False | 0.000 |
| KBMQ_R01 | True | 0.500 | False | 0.000 |
| KBOS_R32 | True | 0.500 | False | 0.000 |
| KBTV_R33-Y | True | 1.000 | False | 0.000 |
| KBUR_R08-Z | True | 0.000 | False | 0.000 |
| KBWC_R26 | True | 0.000 | False | 0.000 |
| KCAG_R07 | True | 0.500 | False | 0.000 |
| KCBE_R05 | True | 0.000 | False | 0.000 |
| KCEA_RNV-D | True | 0.000 | False | 0.000 |
| KCII_R33 | True | 0.500 | False | 0.000 |
| KCOE_R02 | True | 0.500 | False | 0.000 |
| KACT_R32 | True | 1.000 | True | 1.000 |
| KADF_R22 | True | 1.000 | True | 1.000 |
| KAKH_R03 | True | 1.000 | True | 1.000 |
| KANY_R18 | True | 1.000 | True | 1.000 |
| KAOO_R03-Z | True | 1.000 | True | 1.000 |
| KAOO_R21 | True | 1.000 | True | 1.000 |
| KARG_R04 | True | 1.000 | True | 1.000 |
| KATW_R21 | True | 1.000 | True | 1.000 |
| KAVP_R22 | True | 1.000 | True | 1.000 |
| KAWG_R36 | True | 1.000 | True | 1.000 |
| KAXN_R22 | True | 0.750 | True | 1.000 |
| KAXV_R26 | True | 1.000 | True | 1.000 |
| KAZC_R29 | True | 1.000 | True | 1.000 |
| KBFD_R14 | True | 1.000 | True | 1.000 |
| KBJI_R31 | True | 1.000 | True | 1.000 |
| KBKW_R01 | True | 1.000 | True | 1.000 |
| KBKX_R30 | True | 1.000 | True | 1.000 |
| KBLV_R32RY | True | 0.500 | False | 0.000 |
| KBTR_R04L | True | 1.000 | True | 1.000 |
| KBUM_R18 | True | 1.000 | True | 1.000 |
| KBVY_R34 | True | 1.000 | True | 1.000 |
| KBXA_R18 | True | 1.000 | True | 1.000 |
| KBYH_R36 | True | 1.000 | True | 1.000 |
| KBYI_R20 | True | 1.000 | True | 1.000 |
| KCAO_R02 | True | 1.000 | True | 1.000 |
| KCBF_R36 | True | 1.000 | True | 1.000 |
| KCDI_R04 | True | 1.000 | True | 1.000 |
| KCDR_R03 | True | 1.000 | True | 1.000 |
| KCDS_R36 | True | 1.000 | True | 1.000 |
| KCGI_R10 | True | 1.000 | True | 1.000 |
| KCHO_R03 | True | 1.000 | True | 1.000 |
| KCHQ_R36 | True | 1.000 | True | 1.000 |
| KCIC_R13L | True | 1.000 | True | 1.000 |
| KCLL_R11 | True | 1.000 | True | 1.000 |
| KCNC_R10 | True | 1.000 | True | 1.000 |
| KCOI_R11 | True | 0.750 | True | 1.000 |
| KCRS_R32 | True | 1.000 | True | 1.000 |

### Path D

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KABE_I06 | True | 1.000 | False | 0.000 |
| KALS_I02 | True | 1.000 | True | 1.000 |
| KAMA_I04 | True | 0.750 | True | 1.000 |
| KAPC_I01L | True | 1.000 | True | 1.000 |
| KATL_I09R | True | 1.000 | False | 0.000 |
| KAUS_I18L | True | 0.750 | False | 0.500 |
| KAVL_I17 | True | 1.000 | False | 0.000 |
| KAYS_I19-Z | True | 0.750 | False | 0.000 |
| KBMI_I29 | True | 0.750 | True | 1.000 |
| KBUY_I06-Z | True | 1.000 | True | 1.000 |
| KBWG_I03-Y | True | 1.000 | True | 1.000 |
| KCFO_I26 | True | 0.750 | False | 0.500 |
| KCMH_I10R | True | 1.000 | True | 1.000 |
| KAVP_L04 | True | 0.000 | False | 0.000 |
| KAXH_L09 | True | 1.000 | True | 1.000 |
| KBDL_L33 | True | 0.000 | False | 0.000 |
| KBDR_L06 | True | 0.000 | False | 0.000 |
| KBFF_L12 | True | 0.000 | False | 0.000 |
| KBOS_L15R | True | 0.500 | False | 0.000 |
| KBUR_L08-Z | True | 0.000 | False | 0.000 |
| KBYL_L20 | True | 0.000 | False | 0.000 |
| KCEC_L12 | True | 0.000 | False | 0.000 |
| KCFO_L17 | True | 0.500 | False | 0.000 |
| KCOE_L06 | True | 0.000 | False | 0.000 |
| KCRP_L36 | True | 0.000 | False | 0.000 |
| KCRW_L05 | True | 0.000 | False | 0.000 |
| KALN_L29 | True | 0.500 | False | 0.000 |
| KALO_L12 | True | 0.750 | True | 1.000 |
| KAWM_L17 | True | 0.750 | True | 1.000 |
| KBPT_L12 | True | 1.000 | True | 1.000 |
| KBRD_L34 | True | 0.750 | False | 0.000 |
| KBTL_L23R | True | 1.000 | True | 1.000 |
| KBTP_L08 | True | 1.000 | True | 1.000 |
| KBWI_L15L | True | 1.000 | False | 0.000 |
| KCAK_L01 | True | 0.750 | True | 1.000 |
| KCBF_L36 | True | 1.000 | True | 1.000 |
| KCHA_L20 | True | 1.000 | True | 1.000 |
| KCJR_L04 | True | 0.750 | False | 0.500 |
| KAFN_RNV-B | True | 0.500 | False | 0.000 |
| KAFN_RNV-C | True | 0.500 | False | 0.000 |
| KAIB_RNV-A | True | 0.000 | False | 0.000 |
| KANP_RNV-A | True | 0.000 | False | 0.000 |
| KAPT_R04 | True | 0.500 | False | 0.000 |
| KAPV_R18 | True | 0.000 | False | 0.000 |
| KAQW_RNV-A | True | 0.000 | False | 0.000 |
| KAQW_RNV-B | True | 0.000 | False | 0.000 |
| KAVQ_R12 | True | 0.000 | False | 0.000 |
| KAVQ_R21 | True | 0.000 | False | 0.000 |
| KAXH_R27 | True | 1.000 | True | 1.000 |
| KBDH_R31 | True | 0.667 | False | 0.000 |
| KBDN_R34 | True | 0.500 | False | 0.000 |
| KBJC_R12L | True | 0.000 | False | 0.000 |
| KBLF_R05 | True | 0.000 | False | 0.000 |
| KBMQ_R01 | True | 0.500 | False | 0.000 |
| KBOS_R32 | True | 0.500 | False | 0.000 |
| KBTV_R33-Y | True | 0.000 | False | 0.000 |
| KBUR_R08-Z | True | 0.000 | False | 0.000 |
| KBWC_R26 | True | 0.000 | False | 0.000 |
| KCAG_R07 | True | 0.500 | False | 0.000 |
| KCBE_R05 | True | 0.000 | False | 0.000 |
| KCEA_RNV-D | True | 0.000 | False | 0.000 |
| KCII_R33 | True | 0.500 | False | 0.000 |
| KCOE_R02 | True | 0.500 | False | 0.000 |
| KACT_R32 | True | 0.750 | True | 1.000 |
| KADF_R22 | True | 1.000 | True | 1.000 |
| KAKH_R03 | True | 0.750 | True | 1.000 |
| KANY_R18 | True | 1.000 | True | 1.000 |
| KAOO_R03-Z | True | 0.750 | True | 1.000 |
| KAOO_R21 | True | 0.750 | True | 1.000 |
| KARG_R04 | True | 1.000 | True | 1.000 |
| KATW_R21 | True | 1.000 | True | 1.000 |
| KAVP_R22 | True | 1.000 | True | 1.000 |
| KAWG_R36 | True | 1.000 | True | 1.000 |
| KAXN_R22 | True | 0.750 | True | 1.000 |
| KAXV_R26 | True | 1.000 | True | 1.000 |
| KAZC_R29 | True | 1.000 | True | 1.000 |
| KBFD_R14 | True | 1.000 | True | 1.000 |
| KBJI_R31 | True | 1.000 | True | 1.000 |
| KBKW_R01 | True | 1.000 | True | 1.000 |
| KBKX_R30 | True | 1.000 | True | 1.000 |
| KBLV_R32RY | True | 0.500 | False | 0.000 |
| KBTR_R04L | True | 1.000 | True | 1.000 |
| KBUM_R18 | True | 1.000 | True | 1.000 |
| KBVY_R34 | True | 1.000 | True | 1.000 |
| KBXA_R18 | True | 1.000 | True | 1.000 |
| KBYH_R36 | True | 1.000 | True | 1.000 |
| KBYI_R20 | True | 1.000 | True | 1.000 |
| KCAO_R02 | True | 1.000 | True | 1.000 |
| KCBF_R36 | True | 1.000 | True | 1.000 |
| KCDI_R04 | True | 1.000 | True | 1.000 |
| KCDR_R03 | True | 1.000 | True | 1.000 |
| KCDS_R36 | True | 1.000 | True | 1.000 |
| KCGI_R10 | True | 1.000 | True | 1.000 |
| KCHO_R03 | True | 1.000 | True | 1.000 |
| KCHQ_R36 | True | 1.000 | True | 1.000 |
| KCIC_R13L | True | 1.000 | True | 1.000 |
| KCLL_R11 | True | 1.000 | True | 1.000 |
| KCNC_R10 | True | 1.000 | True | 1.000 |
| KCOI_R11 | True | 1.000 | True | 1.000 |
| KCRS_R32 | True | 1.000 | True | 1.000 |

### Path E

| Sample | Output | ScalarExactRate | WaypointsExact | WaypointsJaccard |
|--------|--------|-----------------|----------------|------------------|
| KABE_I06 | True | 0.750 | False | 0.000 |
| KALS_I02 | True | 1.000 | True | 1.000 |
| KAMA_I04 | True | 0.500 | True | 1.000 |
| KAPC_I01L | True | 1.000 | True | 1.000 |
| KATL_I09R | True | 1.000 | False | 0.000 |
| KAUS_I18L | True | 0.000 | False | 0.000 |
| KAVL_I17 | True | 1.000 | False | 0.000 |
| KAYS_I19-Z | True | 0.750 | False | 0.000 |
| KBMI_I29 | True | 0.750 | True | 1.000 |
| KBUY_I06-Z | True | 1.000 | True | 1.000 |
| KBWG_I03-Y | True | 1.000 | True | 1.000 |
| KCFO_I26 | True | 0.750 | False | 0.500 |
| KCMH_I10R | True | 1.000 | True | 1.000 |
| KAVP_L04 | True | 0.000 | False | 0.000 |
| KAXH_L09 | True | 0.667 | True | 1.000 |
| KBDL_L33 | True | 0.000 | False | 0.000 |
| KBDR_L06 | True | 0.000 | False | 0.000 |
| KBFF_L12 | True | 0.000 | False | 0.000 |
| KBOS_L15R | True | 0.500 | False | 0.000 |
| KBUR_L08-Z | True | 0.000 | False | 0.000 |
| KBYL_L20 | True | 0.000 | False | 0.000 |
| KCEC_L12 | True | 0.000 | False | 0.000 |
| KCFO_L17 | True | 0.500 | False | 0.000 |
| KCOE_L06 | True | 0.000 | False | 0.000 |
| KCRP_L36 | True | 0.000 | False | 0.000 |
| KCRW_L05 | True | 0.000 | False | 0.000 |
| KALN_L29 | True | 0.500 | False | 0.000 |
| KALO_L12 | True | 0.750 | True | 1.000 |
| KAWM_L17 | True | 0.750 | True | 1.000 |
| KBPT_L12 | True | 1.000 | True | 1.000 |
| KBRD_L34 | True | 0.750 | False | 0.000 |
| KBTL_L23R | True | 1.000 | True | 1.000 |
| KBTP_L08 | True | 0.750 | True | 1.000 |
| KBWI_L15L | True | 1.000 | False | 0.000 |
| KCAK_L01 | True | 0.750 | True | 1.000 |
| KCBF_L36 | True | 1.000 | True | 1.000 |
| KCHA_L20 | True | 1.000 | True | 1.000 |
| KCJR_L04 | True | 0.750 | True | 1.000 |
| KAFN_RNV-B | True | 0.500 | False | 0.000 |
| KAFN_RNV-C | True | 0.500 | False | 0.000 |
| KAIB_RNV-A | True | 0.000 | False | 0.000 |
| KANP_RNV-A | True | 0.000 | False | 0.000 |
| KAPT_R04 | True | 0.500 | False | 0.000 |
| KAPV_R18 | True | 0.500 | False | 0.000 |
| KAQW_RNV-A | True | 0.000 | False | 0.000 |
| KAQW_RNV-B | True | 0.000 | False | 0.000 |
| KAVQ_R12 | True | 0.000 | False | 0.000 |
| KAVQ_R21 | True | 0.500 | False | 0.000 |
| KAXH_R27 | True | 1.000 | True | 1.000 |
| KBDH_R31 | True | 0.667 | False | 0.000 |
| KBDN_R34 | True | 0.500 | False | 0.000 |
| KBJC_R12L | True | 0.000 | False | 0.000 |
| KBLF_R05 | True | 0.000 | False | 0.000 |
| KBMQ_R01 | True | 0.500 | False | 0.000 |
| KBOS_R32 | True | 0.500 | False | 0.000 |
| KBTV_R33-Y | True | 0.500 | False | 0.000 |
| KBUR_R08-Z | True | 0.000 | False | 0.000 |
| KBWC_R26 | True | 0.000 | False | 0.000 |
| KCAG_R07 | True | 0.500 | False | 0.000 |
| KCBE_R05 | True | 0.000 | False | 0.000 |
| KCEA_RNV-D | True | 0.000 | False | 0.000 |
| KCII_R33 | True | 0.500 | False | 0.000 |
| KCOE_R02 | True | 0.500 | False | 0.000 |
| KACT_R32 | True | 1.000 | True | 1.000 |
| KADF_R22 | True | 1.000 | True | 1.000 |
| KAKH_R03 | True | 1.000 | True | 1.000 |
| KANY_R18 | True | 1.000 | True | 1.000 |
| KAOO_R03-Z | True | 1.000 | True | 1.000 |
| KAOO_R21 | True | 1.000 | True | 1.000 |
| KARG_R04 | True | 1.000 | True | 1.000 |
| KATW_R21 | True | 1.000 | True | 1.000 |
| KAVP_R22 | True | 1.000 | True | 1.000 |
| KAWG_R36 | True | 1.000 | True | 1.000 |
| KAXN_R22 | True | 0.750 | True | 1.000 |
| KAXV_R26 | True | 1.000 | True | 1.000 |
| KAZC_R29 | True | 1.000 | True | 1.000 |
| KBFD_R14 | True | 1.000 | True | 1.000 |
| KBJI_R31 | True | 1.000 | True | 1.000 |
| KBKW_R01 | True | 1.000 | True | 1.000 |
| KBKX_R30 | True | 1.000 | True | 1.000 |
| KBLV_R32RY | True | 0.500 | False | 0.000 |
| KBTR_R04L | True | 1.000 | True | 1.000 |
| KBUM_R18 | True | 1.000 | True | 1.000 |
| KBVY_R34 | True | 1.000 | True | 1.000 |
| KBXA_R18 | True | 1.000 | True | 1.000 |
| KBYH_R36 | True | 1.000 | True | 1.000 |
| KBYI_R20 | True | 1.000 | True | 1.000 |
| KCAO_R02 | True | 1.000 | True | 1.000 |
| KCBF_R36 | True | 1.000 | True | 1.000 |
| KCDI_R04 | True | 1.000 | True | 1.000 |
| KCDR_R03 | True | 1.000 | True | 1.000 |
| KCDS_R36 | True | 1.000 | True | 1.000 |
| KCGI_R10 | True | 1.000 | True | 1.000 |
| KCHO_R03 | True | 1.000 | True | 1.000 |
| KCHQ_R36 | True | 1.000 | True | 1.000 |
| KCIC_R13L | True | 1.000 | True | 1.000 |
| KCLL_R11 | True | 1.000 | True | 1.000 |
| KCNC_R10 | True | 1.000 | True | 1.000 |
| KCOI_R11 | True | 1.000 | True | 1.000 |
| KCRS_R32 | True | 1.000 | True | 1.000 |
