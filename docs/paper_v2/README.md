# paper-v2 documentation namespace

This directory contains the frozen planning, policies, and reviewer-facing documentation for the NeurIPS 2026 Evaluations & Datasets paper-v2 submission package.

This namespace is intentionally separate from the existing first-round ABCDE experiment documentation. Existing issues and PRs remain the engineering foundation; paper-v2 documents define the submission-facing experiment registry, bias controls, artifact release plan, and paper reporting plan.

## Planned files

- `experiment_registry.md` — frozen experiment groups, methods, metrics, and table mapping.
- `claim_evidence_table.md` — evaluative claims, supporting experiments, assumptions, and limits.
- `analysis_plan.md` — analysis freeze before evaluation runs.
- `split_policy.md` — development / evaluation / probe split usage policy.
- `method_registry.md` — method IDs, allowed inputs, forbidden inputs, prompt/model hashes.
- `no_leakage_policy.md` — input-packer and leakage-control policy.
- `source_view_policy.md` — source-view generation and regenerated OCR policy.
- `counterfactual_construction.md` — chart-to-424 counterfactual construction policy.
- `statistical_reporting_policy.md` — bootstrap and paired-delta reporting policy.
- `reproducibility_checklist.md` — final reproducibility checklist.

## Related issues

- PV2-00: #33
- PV2-01: #34
- PV2-02: #35
- PV2-03: #36
- PV2-14: #47
- PV2-18: #51
