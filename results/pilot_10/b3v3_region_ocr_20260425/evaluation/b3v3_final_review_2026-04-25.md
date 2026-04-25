# B3V3 Final Review - 2026-04-25

## Scope

This review covers the B3V3 execution loop for the 10-chart pilot set.

The work intentionally changed the automatic generation flow only. It did not manually edit final JSON answers or copy canonical target values into predictions.

## Final Result

| Metric | Before this loop | Final B3V3 |
|---|---:|---:|
| Coverage | 1.000 | 1.000 |
| LegCountAcc | 0.900 | 0.900 |
| QFieldAcc | 0.688 | 0.887 |
| Precision | 0.770 | 0.949 |
| Recall | 0.593 | 0.823 |
| F1 | 0.670 | 0.882 |
| ChartExact | 0.000 | 0.200 |
| ExtraPredLegs | 2 | 2 |
| MissingPredLegs | 0 | 0 |

Final per-field exact accuracy:

| Field | Accuracy |
|---|---:|
| Q_terminator | 0.968 |
| Q1_fix_ident | 0.968 |
| Q2_altitude_constraint | 0.871 |
| Q3_turn | 0.935 |
| Q4_course_or_radial | 0.742 |
| Q5_hold_params | 0.839 |

## Flow Changes Reviewed

- B3V3 candidate legs now provide scalar preferred `Q_terminator` values instead of broad alternatives.
- The postprocessor aligns method output to OCR-derived `candidate_legs`, preventing LLM over-splitting of visual cells into extra canonical legs.
- Candidate hints are now used consistently for Q2/Q3/Q4/Q5 when they are generated from chart OCR or visual-cell evidence.
- OCR tolerance was added for `climbing 1 1000`, `left rn`, split `tr 284 to TELLE` cells, and fuzzy `4qu..` missed-approach-fix distance.
- Hold-parameter extraction was tightened to avoid treating MSA `25 NM` as hold distance.
- The broad reciprocal-course fallback was removed after review because it produced false hold inbound courses from unrelated chart text.

## Validation

- Prompt no-leakage validation: PASS for all 10 B3V3 prompt inputs.
- Bbox normalization validation: PASS, 820 bbox objects checked.
- Method output validation: PASS for all 10 B3V3 outputs.
- PR #28 official schema validation: PASS for all 10 B3V3 outputs.
- Final scoring was rerun after every accepted flow change.

## Remaining Errors

Final B3V3 has 22 remaining scoring errors:

- 8 are `Q4_course_or_radial`, mostly initial CA course values not visible in the current B3 missed-approach-detail evidence.
- 5 are `Q5_hold_params`, mostly missed-approach-fix inbound courses lost by OCR in the inset.
- 4 are `Q2_altitude_constraint`, mostly initial CA altitude values derived from profile/minima/runway context outside the current B3 crop scope.
- 2 are `Q3_turn`, where OCR/visual direction evidence is insufficient for the turn direction.
- 5 chart-level errors are concentrated in `KBOS_L15R`, where the CIFP-derived target encodes the procedure as a single HM leg while the visible chart text naturally decomposes into climb/radial/hold legs.

## Review Decision

No further automatic rule was added after the third rerun because the remaining safe improvements require broader OCR/input evidence, not more answer-shaped postprocessing.

Recommended next optimization is to extend B3 input crops to include profile/minima/runway-course and missed-approach-fix inset OCR at higher resolution. That should target the remaining initial CA Q2/Q4 and hold inbound-course errors without leaking canonical JSON.
