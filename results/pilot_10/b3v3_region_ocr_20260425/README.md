# B3V3 Region-Aware OCR Pilot-10 Results

This directory contains a reviewable pilot result package for the B-group missed-approach extraction experiment.

## Summary

| Method | Coverage | LegCountAcc | QFieldAcc | Precision | Recall | F1 | ChartExact |
|---|---:|---:|---:|---:|---:|---:|---:|
| B1 | 1.000 | 0.500 | 0.495 | 0.560 | 0.451 | 0.500 | 0.000 |
| B3 | 1.000 | 0.200 | 0.344 | 0.422 | 0.310 | 0.357 | 0.000 |
| B3V2 | 1.000 | 0.800 | 0.484 | 0.621 | 0.522 | 0.567 | 0.000 |
| B3V3 | 1.000 | 0.900 | 0.887 | 0.949 | 0.823 | 0.882 | 0.200 |

## Directory Contents

| Directory/File | Description |
|---|---|
| `RUN_SUMMARY.md` | Execution-loop summary for the final B3V3 run |
| `evaluation/` | Human-readable and machine-readable evaluation outputs |
| `method_outputs/` | Final B3V3 `missed_approach_leg_v1` JSON outputs |
| `candidate_legs/` | OCR-derived candidate legs used by B3V3 |
| `evidence_traces/` | Field-level evidence traces linking outputs to OCR/cell evidence |
| `reference_targets/` | CIFP-derived proxy targets used by the scorer only |
| `schemas/` | Schema snapshot used for PR #28 validation |
| `semantic_candidate_manifest.json` | Manifest for B3V3 semantic candidate files |
| `evidence_trace_manifest.json` | Manifest for evidence trace files |
| `MANIFEST.sha256` | SHA256 checksum manifest for the result package |

## No-Leakage Boundary

The extraction prompts and method outputs were generated without using the CIFP-derived target JSON, expected field values, manually corrected answers, or boxed-preview images. The `reference_targets/` files are included only so reviewers can inspect the scoring reference used for this pilot.

## Not Included

Raw chart images, boxed preview images, FAA CIFP source archives, temporary OCR caches, and local run logs are not included here. This keeps the PR lightweight and avoids mixing review artifacts with method inputs.
