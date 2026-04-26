# paper-v2 derived benchmark export namespace

This directory is the intended read-only data entry point for paper-v2 experiments.

All formal paper-v2 runners should read through `MANIFEST.json` and the files listed here rather than directly reading legacy paths, pilot outputs, or temporary annotation-platform internals.

## Planned data artifacts

- `MANIFEST.json` — version, source commits, source issues/PRs, split counts, checksums, schema version.
- `sample_manifest.jsonl` — chart-level sample records and source paths.
- `splits.json` — development / evaluation / probe split lock.
- `field_targets.jsonl` — field-level target expansion for scoring.
- `roi_manifest.jsonl` — ROI records with prelabel/human status.
- `gold_ma_text.jsonl` — human-corrected missed-approach prose only.
- `evidence_provenance.jsonl` — frozen evidence buckets.
- `challenge_tags.jsonl` — frozen challenge tags.
- `gold_observable_evidence.jsonl` — visible chart facts for oracle diagnostics.
- `verification_counterfactuals.jsonl` — chart-to-424 verification cases.
- `checksums.sha256` — file checksums for the derived export.
- `source_views/` — generated source-view images and manifests.

## Related issues

- PV2-02: #35
- PV2-04: #37
- PV2-05: #38
- PV2-06: #39
- PV2-07: #40
- PV2-12: #45
