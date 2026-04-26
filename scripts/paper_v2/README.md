# paper-v2 script namespace

This directory is reserved for paper-v2 scripts. Scripts here should read from frozen paper-v2 manifests and write to paper-v2 prediction/report directories.

Do not modify legacy `data/`, `results/`, or first-round ABCDE outputs in paper-v2 scripts unless an issue explicitly authorizes that migration.

## Planned scripts

- `build_v2_export.py` — materialize `benchmark_exports/derived/v2/` from existing repo assets.
- `build_source_views.py` — generate source-view images and masks.
- `validate_no_leakage.py` — validate input manifests against forbidden fields.
- `build_424_counterfactuals.py` — generate chart-to-424 verification cases.
- `score_extraction.py` — score canonical extraction outputs.
- `score_by_evidence_source.py` — compute evidence-bucket breakdowns.
- `score_by_challenge_tags.py` — compute challenge split metrics.
- `bootstrap_metrics.py` — chart/procedure-level bootstrap CIs.
- `paired_delta_ci.py` — paired method/source-view deltas.

## Related issues

- PV2-04: #37
- PV2-07: #40
- PV2-09: #42
- PV2-10: #43
- PV2-12: #45
- PV2-14: #47
- PV2-16: #49
