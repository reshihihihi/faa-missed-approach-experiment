# paper-v2 report namespace

This directory stores paper-v2 reports, quality-control summaries, and paper-ready tables.

Reports here should be generated from frozen predictions, scorers, and manifests. Avoid hand-editing table values; if a table must be manually curated for the paper, keep the generated source table next to it.

## Planned reports

- `paper_tables/` — main paper tables.
- `appendix_tables/` — full matrices and appendix tables.
- `no_leakage_report.json` — input-packer leakage validation.
- `annotation_reliability_report.md` — annotation reliability and adjudication summary.
- `bootstrap_ci.csv` — point estimates and bootstrap CIs.
- `paired_delta_ci.csv` — paired method/view deltas.
- `source_ablation_report.md` — source-view ablation interpretation.
- `counterfactual_qc_report.md` — chart-to-424 counterfactual QC.

## Related issues

- PV2-08: #41
- PV2-09: #42
- PV2-10: #43
- PV2-11: #44
- PV2-12: #45
- PV2-14: #47
- PV2-15: #48
- PV2-16: #49
- PV2-18: #51
