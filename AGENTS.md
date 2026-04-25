# AGENTS.md

This repository contains a reproducible FAA missed-approach extraction experiment.
When reviewing pull requests, prefer findings that affect scientific validity,
reproducibility, data integrity, and operational correctness.

## Review Priorities

Focus on:

- correctness bugs in extraction, evaluation, and error-analysis logic
- reproducibility regressions in dataset materialization and path handling
- accidental changes to the committed formal split under `data/v2604_100/`
- mismatches between documented workflow and actual script behavior
- unsafe handling of external downloads, credentials, and file overwrites
- changes that silently alter published metrics or result interpretation

## Repository Map

- `scripts/build_dataset_100.py`
  Public FAA data bootstrap and local materialization flow.
- `scripts/run_O.py`
  CIFP-derived reference baseline.
- `scripts/run_A.py`, `scripts/run_B.py`
  OCR-based extraction paths.
- `scripts/run_C.py`, `scripts/run_C_QA.py`, `scripts/run_D.py`, `scripts/run_E.py`
  Image-direct extraction paths.
- `evaluate.py`
  Recomputes metrics and aggregate reports.
- `error_analysis.py`
  Produces post-hoc error analysis outputs.
- `data/v2604_100/`
  Formal 100-sample committed manifest, pair data, and selection metadata.
- `results/v2604_100/`
  Published formal outputs and reports that should not drift accidentally.
- `prompts/`
  Prompt assets for LLM-based paths.

## What Reviewers Should Treat As High Risk

- changing the meaning or schema of generated JSON outputs
- modifying sample selection logic without updating committed metadata and docs
- changing path resolution in ways that break non-`E:/experiment` usage
- edits that make reruns depend on private local files or hidden environment state
- updates to prompts or parsers that may improve one path while invalidating comparisons
- edits to committed reports or metrics without a reproducible rerun explanation

## Pull Request Expectations

Each PR should explain:

- which scripts or paths are affected
- whether the formal `v2604_100` split or outputs change
- whether rerunning `scripts/smoke_test.py` is enough, or a full experiment rerun is needed
- whether prompts, metrics, or published reports changed
- what commands were used for verification

## Preferred Review Style

- Prefer concrete findings over stylistic suggestions.
- Flag undocumented behavior changes even if the code still runs.
- Ask for regenerated metrics when evaluation-affecting code changes.
- Be conservative about approving edits to `data/v2604_100/` and `results/v2604_100/`.
