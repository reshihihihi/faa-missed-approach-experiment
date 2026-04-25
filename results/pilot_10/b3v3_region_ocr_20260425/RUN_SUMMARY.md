# B3V3 Terminator/Hold Fix Run Summary

Run ID: `run_20260425_terminator_hold_fix`

Date: 2026-04-25

Scope: Improve B3V3 automatic extraction flow, rerun the 10-chart pilot experiment, review remaining errors, and stop only after unsafe answer-shaped optimizations were ruled out.

## Changed Scripts

- `scripts/build_b3v3_semantic_candidates.py` in the local experiment workspace
- `scripts/run_llm_extraction.py` in the local experiment workspace

## Main Changes

- Replaced multi-choice path-terminator hints with scalar OCR-rule preferred values.
- Added B3V3 candidate-leg postprocessing so leg order/count and candidate-supported fields remain consistent after LLM extraction.
- Added OCR-tolerant parsing for split track cells, OCR-damaged turn text, spaced altitude text, and fuzzy missed-approach-fix distance text.
- Tightened hold-distance extraction so MSA distances are not mistaken for missed-approach hold distances.
- Removed one over-broad course fallback during review because it introduced unrelated inbound courses.

## Final Validation

- Prompt no-leakage: PASS.
- Bbox normalization: PASS, 820 bbox objects.
- Method output validation: PASS for all 10 B3V3 outputs.
- PR #28 official schema: PASS for all 10 B3V3 outputs.

## Final Metrics

| Metric | Final B3V3 |
|---|---:|
| Coverage | 1.000 |
| LegCountAcc | 0.900 |
| QFieldAcc | 0.887 |
| Precision | 0.949 |
| Recall | 0.823 |
| F1 | 0.882 |
| ChartExact | 0.200 |
| ExtraPredLegs | 2 |
| MissingPredLegs | 0 |

## Important Logs

- `12_run_llm_extraction_B3V3_force.log`
- `32_run_llm_extraction_B3V3_second_force.log`
- `42_run_llm_extraction_B3V3_third_force.log`
- `47_score_extended_third.log`
- `48_error_breakdown_final.log`

## Final Review

Full review: `evaluation/b3v3_final_review_2026-04-25.md`
