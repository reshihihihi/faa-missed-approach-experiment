# Error Type Analysis

Reference baseline: Path O

Error taxonomy:
- scalar field errors: missing, wrong value, or spurious prediction
- waypoint errors: missed all, missing points, extra points, mixed missing+extra, or spurious only
- sample-level signatures: the most common combinations of errors on the same sample

## Path A

### Major Error Types

| ErrorType | Count | Coverage | ExampleSamples |
|-----------|-------|----------|----------------|
| holding_required:false_hold | 30 | 30.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBOS_L15R, KBUR_L08-Z |
| climb_altitude:spurious_prediction | 29 | 29.0% | KAVP_L04, KBDR_L06, KBFF_L12, KBOS_L15R, KCFO_L17 |
| waypoints:spurious_only | 29 | 29.0% | KABE_I06, KATL_I09R, KBDR_L06, KBOS_L15R, KCEC_L12 |
| holding_fix:spurious_prediction | 26 | 26.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBOS_L15R, KCFO_L17 |
| turn_direction:hallucinated_turn | 24 | 24.0% | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |
| holding_fix:missing_prediction | 17 | 17.0% | KAMA_I04, KAPC_I01L, KAVL_I17, KBWG_I03-Y, KCMH_I10R |
| waypoints:missed_all | 15 | 15.0% | KALS_I02, KAMA_I04, KAPC_I01L, KBMI_I29, KBUY_I06-Z |
| holding_required:missed_hold | 14 | 14.0% | KAMA_I04, KBWG_I03-Y, KCMH_I10R, KBPT_L12, KCHA_L20 |
| waypoints:noisy_mismatch | 13 | 13.0% | KAUS_I18L, KAYS_I19-Z, KBWG_I03-Y, KCMH_I10R, KAWM_L17 |
| holding_fix:wrong_fix | 8 | 8.0% | KAUS_I18L, KAYS_I19-Z, KAWM_L17, KBRD_L34, KBTL_L23R |
| climb_altitude:wrong_value | 7 | 7.0% | KAMA_I04, KBWG_I03-Y, KCMH_I10R, KALN_L29, KBWI_L15L |
| waypoints:extra_points | 7 | 7.0% | KALN_L29, KAXH_R27, KAKH_R03, KARG_R04, KBFD_R14 |

### By Field

#### climb_altitude

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| climb_altitude:spurious_prediction | 29 | KAVP_L04, KBDR_L06, KBFF_L12, KBOS_L15R, KCFO_L17 |
| climb_altitude:wrong_value | 7 | KAMA_I04, KBWG_I03-Y, KCMH_I10R, KALN_L29, KBWI_L15L |
| climb_altitude:missing_prediction | 5 | KBPT_L12, KBLV_R32RY, KBUM_R18, KCDR_R03, KCHQ_R36 |

#### turn_direction

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| turn_direction:hallucinated_turn | 24 | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |
| turn_direction:missed_turn | 6 | KAPC_I01L, KAYS_I19-Z, KBWG_I03-Y, KBPT_L12, KAZC_R29 |

#### holding_required

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_required:false_hold | 30 | KAVP_L04, KBDL_L33, KBDR_L06, KBOS_L15R, KBUR_L08-Z |
| holding_required:missed_hold | 14 | KAMA_I04, KBWG_I03-Y, KCMH_I10R, KBPT_L12, KCHA_L20 |

#### holding_fix

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_fix:spurious_prediction | 26 | KAVP_L04, KBDL_L33, KBDR_L06, KBOS_L15R, KCFO_L17 |
| holding_fix:missing_prediction | 17 | KAMA_I04, KAPC_I01L, KAVL_I17, KBWG_I03-Y, KCMH_I10R |
| holding_fix:wrong_fix | 8 | KAUS_I18L, KAYS_I19-Z, KAWM_L17, KBRD_L34, KBTL_L23R |

#### waypoints

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| waypoints:spurious_only | 29 | KABE_I06, KATL_I09R, KBDR_L06, KBOS_L15R, KCEC_L12 |
| waypoints:missed_all | 15 | KALS_I02, KAMA_I04, KAPC_I01L, KBMI_I29, KBUY_I06-Z |
| waypoints:noisy_mismatch | 13 | KAUS_I18L, KAYS_I19-Z, KBWG_I03-Y, KCMH_I10R, KAWM_L17 |
| waypoints:extra_points | 7 | KALN_L29, KAXH_R27, KAKH_R03, KARG_R04, KBFD_R14 |
| waypoints:missing_points | 1 | KCOI_R11 |

### Common Sample-Level Error Patterns

| Pattern | Count | ExampleSamples |
|---------|-------|----------------|
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | waypoints:spurious_only | 13 | KBOS_L15R, KCFO_L17, KAFN_RNV-B, KAFN_RNV-C, KAPT_R04 |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | turn_direction:hallucinated_turn | waypoints:spurious_only | 9 | KBDR_L06, KAIB_RNV-A, KANP_RNV-A, KAQW_RNV-A, KAVQ_R12 |
| waypoints:extra_points | 6 | KAXH_R27, KAKH_R03, KARG_R04, KBFD_R14, KBYI_R20 |
| waypoints:spurious_only | 5 | KABE_I06, KATL_I09R, KCEC_L12, KAQW_RNV-B, KCBE_R05 |
| holding_fix:missing_prediction | holding_required:missed_hold | waypoints:missed_all | 4 | KCHA_L20, KAXV_R26, KBJI_R31, KCDI_R04 |
| holding_fix:wrong_fix | waypoints:noisy_mismatch | 4 | KBRD_L34, KBTL_L23R, KCBF_L36, KCIC_R13L |
| turn_direction:hallucinated_turn | 4 | KCFO_I26, KALO_L12, KCJR_L04, KAXN_R22 |
| climb_altitude:missing_prediction | holding_fix:missing_prediction | holding_required:missed_hold | waypoints:noisy_mismatch | 2 | KBLV_R32RY, KCDR_R03 |

## Path B

### Major Error Types

| ErrorType | Count | Coverage | ExampleSamples |
|-----------|-------|----------|----------------|
| waypoints:spurious_only | 40 | 40.0% | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| turn_direction:wrong_direction | 38 | 38.0% | KAPC_I01L, KATL_I09R, KAVL_I17, KBOS_L15R, KAFN_RNV-B |
| holding_fix:spurious_prediction | 36 | 36.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| holding_required:false_hold | 36 | 36.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| climb_altitude:spurious_prediction | 34 | 34.0% | KAVP_L04, KBDR_L06, KBFF_L12, KBOS_L15R, KBUR_L08-Z |
| turn_direction:hallucinated_turn | 31 | 31.0% | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |
| waypoints:extra_points | 7 | 7.0% | KAMA_I04, KAUS_I18L, KCFO_I26, KALN_L29, KALO_L12 |
| holding_fix:wrong_fix | 5 | 5.0% | KAYS_I19-Z, KBRD_L34, KBTL_L23R, KBLV_R32RY, KCIC_R13L |
| waypoints:noisy_mismatch | 5 | 5.0% | KAYS_I19-Z, KBRD_L34, KBTL_L23R, KBLV_R32RY, KCIC_R13L |
| climb_altitude:wrong_value | 4 | 4.0% | KAYS_I19-Z, KALN_L29, KCHA_L20, KAZC_R29 |

### By Field

#### climb_altitude

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| climb_altitude:spurious_prediction | 34 | KAVP_L04, KBDR_L06, KBFF_L12, KBOS_L15R, KBUR_L08-Z |
| climb_altitude:wrong_value | 4 | KAYS_I19-Z, KALN_L29, KCHA_L20, KAZC_R29 |

#### turn_direction

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| turn_direction:wrong_direction | 38 | KAPC_I01L, KATL_I09R, KAVL_I17, KBOS_L15R, KAFN_RNV-B |
| turn_direction:hallucinated_turn | 31 | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |

#### holding_required

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_required:false_hold | 36 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |

#### holding_fix

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_fix:spurious_prediction | 36 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| holding_fix:wrong_fix | 5 | KAYS_I19-Z, KBRD_L34, KBTL_L23R, KBLV_R32RY, KCIC_R13L |

#### waypoints

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| waypoints:spurious_only | 40 | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| waypoints:extra_points | 7 | KAMA_I04, KAUS_I18L, KCFO_I26, KALN_L29, KALO_L12 |
| waypoints:noisy_mismatch | 5 | KAYS_I19-Z, KBRD_L34, KBTL_L23R, KBLV_R32RY, KCIC_R13L |

### Common Sample-Level Error Patterns

| Pattern | Count | ExampleSamples |
|---------|-------|----------------|
| turn_direction:wrong_direction | 23 | KAPC_I01L, KAXH_R27, KACT_R32, KAKH_R03, KAOO_R03-Z |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | turn_direction:hallucinated_turn | waypoints:spurious_only | 19 | KAVP_L04, KBDR_L06, KBFF_L12, KBUR_L08-Z, KBYL_L20 |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | turn_direction:wrong_direction | waypoints:spurious_only | 11 | KBOS_L15R, KAFN_RNV-B, KAPT_R04, KAPV_R18, KAQW_RNV-B |
| turn_direction:hallucinated_turn | waypoints:extra_points | 5 | KAMA_I04, KAUS_I18L, KCFO_I26, KALO_L12, KCJR_L04 |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | waypoints:spurious_only | 4 | KCFO_L17, KAFN_RNV-C, KCII_R33, KCOE_R02 |
| turn_direction:hallucinated_turn | 4 | KBMI_I29, KAWM_L17, KCAK_L01, KAXN_R22 |
| climb_altitude:wrong_value | 2 | KCHA_L20, KAZC_R29 |
| holding_fix:wrong_fix | waypoints:noisy_mismatch | 2 | KBRD_L34, KBTL_L23R |

## Path C

### Major Error Types

| ErrorType | Count | Coverage | ExampleSamples |
|-----------|-------|----------|----------------|
| waypoints:spurious_only | 40 | 40.0% | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| climb_altitude:spurious_prediction | 35 | 35.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| holding_fix:spurious_prediction | 35 | 35.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| holding_required:false_hold | 35 | 35.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| turn_direction:hallucinated_turn | 32 | 32.0% | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |
| holding_fix:wrong_fix | 4 | 4.0% | KAYS_I19-Z, KBRD_L34, KBLV_R32RY, KCOI_R11 |
| waypoints:noisy_mismatch | 4 | 4.0% | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| holding_fix:missing_prediction | 1 | 1.0% | KCMH_I10R |
| waypoints:extra_points | 1 | 1.0% | KCFO_I26 |

### By Field

#### climb_altitude

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| climb_altitude:spurious_prediction | 35 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |

#### turn_direction

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| turn_direction:hallucinated_turn | 32 | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |

#### holding_required

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_required:false_hold | 35 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |

#### holding_fix

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_fix:spurious_prediction | 35 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| holding_fix:wrong_fix | 4 | KAYS_I19-Z, KBRD_L34, KBLV_R32RY, KCOI_R11 |
| holding_fix:missing_prediction | 1 | KCMH_I10R |

#### waypoints

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| waypoints:spurious_only | 40 | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| waypoints:noisy_mismatch | 4 | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| waypoints:extra_points | 1 | KCFO_I26 |

### Common Sample-Level Error Patterns

| Pattern | Count | ExampleSamples |
|---------|-------|----------------|
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | turn_direction:hallucinated_turn | waypoints:spurious_only | 21 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBUR_L08-Z |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | waypoints:spurious_only | 13 | KBOS_L15R, KCFO_L17, KAFN_RNV-B, KAFN_RNV-C, KAPT_R04 |
| turn_direction:hallucinated_turn | 8 | KAMA_I04, KAUS_I18L, KBMI_I29, KALO_L12, KAWM_L17 |
| waypoints:spurious_only | 4 | KABE_I06, KATL_I09R, KAVL_I17, KBWI_L15L |
| holding_fix:wrong_fix | waypoints:noisy_mismatch | 2 | KAYS_I19-Z, KBRD_L34 |
| climb_altitude:spurious_prediction | waypoints:spurious_only | 1 | KBTV_R33-Y |
| holding_fix:missing_prediction | 1 | KCMH_I10R |
| holding_fix:spurious_prediction | holding_required:false_hold | waypoints:spurious_only | 1 | KBDH_R31 |

## Path D

### Major Error Types

| ErrorType | Count | Coverage | ExampleSamples |
|-----------|-------|----------|----------------|
| waypoints:spurious_only | 40 | 40.0% | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| holding_fix:spurious_prediction | 36 | 36.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| holding_required:false_hold | 36 | 36.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| climb_altitude:spurious_prediction | 35 | 35.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| turn_direction:hallucinated_turn | 34 | 34.0% | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |
| turn_direction:wrong_direction | 5 | 5.0% | KAPV_R18, KAVQ_R21, KBTV_R33-Y, KACT_R32, KAKH_R03 |
| holding_fix:wrong_fix | 4 | 4.0% | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| waypoints:noisy_mismatch | 4 | 4.0% | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| waypoints:extra_points | 3 | 3.0% | KAUS_I18L, KCFO_I26, KCJR_L04 |

### By Field

#### climb_altitude

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| climb_altitude:spurious_prediction | 35 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |

#### turn_direction

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| turn_direction:hallucinated_turn | 34 | KAMA_I04, KAUS_I18L, KBMI_I29, KCFO_I26, KAVP_L04 |
| turn_direction:wrong_direction | 5 | KAPV_R18, KAVQ_R21, KBTV_R33-Y, KACT_R32, KAKH_R03 |

#### holding_required

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_required:false_hold | 36 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |

#### holding_fix

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_fix:spurious_prediction | 36 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| holding_fix:wrong_fix | 4 | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |

#### waypoints

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| waypoints:spurious_only | 40 | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| waypoints:noisy_mismatch | 4 | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| waypoints:extra_points | 3 | KAUS_I18L, KCFO_I26, KCJR_L04 |

### Common Sample-Level Error Patterns

| Pattern | Count | ExampleSamples |
|---------|-------|----------------|
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | turn_direction:hallucinated_turn | waypoints:spurious_only | 21 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBUR_L08-Z |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | waypoints:spurious_only | 11 | KBOS_L15R, KCFO_L17, KAFN_RNV-B, KAFN_RNV-C, KAPT_R04 |
| turn_direction:hallucinated_turn | 8 | KAMA_I04, KBMI_I29, KALO_L12, KAWM_L17, KCAK_L01 |
| waypoints:spurious_only | 4 | KABE_I06, KATL_I09R, KAVL_I17, KBWI_L15L |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | turn_direction:wrong_direction | waypoints:spurious_only | 3 | KAPV_R18, KAVQ_R21, KBTV_R33-Y |
| turn_direction:hallucinated_turn | waypoints:extra_points | 3 | KAUS_I18L, KCFO_I26, KCJR_L04 |
| holding_fix:wrong_fix | turn_direction:hallucinated_turn | waypoints:noisy_mismatch | 2 | KALN_L29, KBLV_R32RY |
| holding_fix:wrong_fix | waypoints:noisy_mismatch | 2 | KAYS_I19-Z, KBRD_L34 |

## Path E

### Major Error Types

| ErrorType | Count | Coverage | ExampleSamples |
|-----------|-------|----------|----------------|
| waypoints:spurious_only | 40 | 40.0% | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| holding_fix:spurious_prediction | 37 | 37.0% | KAVP_L04, KAXH_L09, KBDL_L33, KBDR_L06, KBFF_L12 |
| holding_required:false_hold | 37 | 37.0% | KAVP_L04, KAXH_L09, KBDL_L33, KBDR_L06, KBFF_L12 |
| climb_altitude:spurious_prediction | 35 | 35.0% | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| turn_direction:hallucinated_turn | 31 | 31.0% | KAMA_I04, KBMI_I29, KCFO_I26, KAVP_L04, KBDL_L33 |
| holding_fix:wrong_fix | 5 | 5.0% | KABE_I06, KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| waypoints:noisy_mismatch | 4 | 4.0% | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| climb_altitude:wrong_value | 2 | 2.0% | KAMA_I04, KBTP_L08 |
| climb_altitude:missing_prediction | 1 | 1.0% | KAUS_I18L |
| holding_fix:missing_prediction | 1 | 1.0% | KAUS_I18L |
| holding_required:missing_prediction | 1 | 1.0% | KAUS_I18L |
| turn_direction:missing_prediction | 1 | 1.0% | KAUS_I18L |

### By Field

#### climb_altitude

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| climb_altitude:spurious_prediction | 35 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBOS_L15R |
| climb_altitude:wrong_value | 2 | KAMA_I04, KBTP_L08 |
| climb_altitude:missing_prediction | 1 | KAUS_I18L |

#### turn_direction

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| turn_direction:hallucinated_turn | 31 | KAMA_I04, KBMI_I29, KCFO_I26, KAVP_L04, KBDL_L33 |
| turn_direction:missing_prediction | 1 | KAUS_I18L |

#### holding_required

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_required:false_hold | 37 | KAVP_L04, KAXH_L09, KBDL_L33, KBDR_L06, KBFF_L12 |
| holding_required:missing_prediction | 1 | KAUS_I18L |

#### holding_fix

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| holding_fix:spurious_prediction | 37 | KAVP_L04, KAXH_L09, KBDL_L33, KBDR_L06, KBFF_L12 |
| holding_fix:wrong_fix | 5 | KABE_I06, KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| holding_fix:missing_prediction | 1 | KAUS_I18L |

#### waypoints

| ErrorType | Count | ExampleSamples |
|-----------|-------|----------------|
| waypoints:spurious_only | 40 | KABE_I06, KATL_I09R, KAVL_I17, KAVP_L04, KBDL_L33 |
| waypoints:noisy_mismatch | 4 | KAYS_I19-Z, KALN_L29, KBRD_L34, KBLV_R32RY |
| waypoints:extra_points | 1 | KCFO_I26 |
| waypoints:missed_all | 1 | KAUS_I18L |

### Common Sample-Level Error Patterns

| Pattern | Count | ExampleSamples |
|---------|-------|----------------|
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | turn_direction:hallucinated_turn | waypoints:spurious_only | 21 | KAVP_L04, KBDL_L33, KBDR_L06, KBFF_L12, KBUR_L08-Z |
| climb_altitude:spurious_prediction | holding_fix:spurious_prediction | holding_required:false_hold | waypoints:spurious_only | 14 | KBOS_L15R, KCFO_L17, KAFN_RNV-B, KAFN_RNV-C, KAPT_R04 |
| turn_direction:hallucinated_turn | 6 | KBMI_I29, KALO_L12, KAWM_L17, KCAK_L01, KCJR_L04 |
| waypoints:spurious_only | 3 | KATL_I09R, KAVL_I17, KBWI_L15L |
| holding_fix:wrong_fix | turn_direction:hallucinated_turn | waypoints:noisy_mismatch | 2 | KALN_L29, KBLV_R32RY |
| holding_fix:wrong_fix | waypoints:noisy_mismatch | 2 | KAYS_I19-Z, KBRD_L34 |
| climb_altitude:missing_prediction | holding_fix:missing_prediction | holding_required:missing_prediction | turn_direction:missing_prediction | waypoints:missed_all | 1 | KAUS_I18L |
| climb_altitude:wrong_value | 1 | KBTP_L08 |
