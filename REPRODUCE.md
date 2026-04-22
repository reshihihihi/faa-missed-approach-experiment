# Reproduction Guide

This document explains how to reproduce the formal 100-sample experiment in this repository.

## 1. Reproduction Target

The reproduction target is the formal dataset and result setting under:

- `data/v2604_100/`
- `results/v2604_100/`

This repository does not ask you to rediscover a new 100-sample split. The formal split is already fixed and committed through:

- `data/v2604_100/sample_manifest_100.json`
- `data/v2604_100/pairs_100.json`
- `data/v2604_100/selection_100.json`

In other words, reproduction here means:

1. regenerate the missing public raw FAA inputs locally
2. rerun the extraction paths on the same committed 100 samples
3. rerun evaluation and error analysis

## 2. What Is Already Included

The repository already includes:

- the formal 100-sample manifest
- the committed paired structured CIFP procedure data
- the prompts for all LLM paths
- the current formal reports and metrics

The repository does not include the large raw inputs by default:

- chart PDFs
- rendered chart PNGs
- FAA CIFP archive contents

Those are recreated locally from public FAA sources.

## 3. Environment Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run a quick repository self-check:

```bash
python scripts/smoke_test.py
```

Expected result:

- the script should report 100 manifest entries
- the script should report 100 pair entries
- the script should end with `Smoke test passed.`

## 4. Download and Materialize Public FAA Inputs

Run:

```bash
python scripts/build_dataset_100.py
```

This script performs the reproducibility-critical bootstrap:

1. downloads the official FAA CIFP archive for cycle `2604`
2. extracts `FAACIFP18` into `data/v2604_100/cifp/`
3. downloads the FAA d-TPP metafile for traceability
4. downloads the 100 chart PDFs referenced by the committed manifest
5. renders page 1 of each PDF to the expected PNG filename under `data/v2604_100/charts/`

Useful optional flags:

```bash
python scripts/build_dataset_100.py --skip-downloads
python scripts/build_dataset_100.py --skip-render
python scripts/build_dataset_100.py --force-render
```

After a successful run, the following local directories should exist:

- `data/v2604_100/sources/`
- `data/v2604_100/cifp/`
- `data/v2604_100/pdfs/`
- `data/v2604_100/charts/`

The script also writes:

- `data/v2604_100/materialization_report.json`

## 5. Configure Model Credentials

Paths `B`, `C`, `D`, and `E` require Anthropic-compatible credentials.

Use either:

```bash
ANTHROPIC_API_KEY=...
```

or:

```bash
ANTHROPIC_AUTH_TOKEN=...
ANTHROPIC_BASE_URL=...
```

Example PowerShell:

```powershell
$env:ANTHROPIC_AUTH_TOKEN="your_token"
$env:ANTHROPIC_BASE_URL="https://your-compatible-endpoint"
```

## 6. Run the Formal Experiment

Reference baseline:

```bash
python scripts/run_O.py
```

OCR paths:

```bash
python scripts/run_A.py
python scripts/run_B.py
```

Image-direct paths:

```bash
python scripts/run_C.py
python scripts/run_D.py
python scripts/run_E.py
```

Then recompute metrics and error analysis:

```bash
python evaluate.py
python error_analysis.py
```

## 7. Expected Output Locations

Formal outputs are written under:

- `results/v2604_100/O/`
- `results/v2604_100/A/`
- `results/v2604_100/B/`
- `results/v2604_100/C/`
- `results/v2604_100/D/`
- `results/v2604_100/E/`

Reports are written to:

- `results/v2604_100/evaluation_report.md`
- `results/v2604_100/all_metrics.json`
- `results/v2604_100/error_analysis_report.md`
- `results/v2604_100/error_analysis.json`

## 8. What Changed To Improve Reproducibility

The main reproducibility fixes in the current repository state are:

1. Core scripts no longer require the repository to live at `E:/experiment`.
2. Evaluation scripts no longer rely on hard-coded absolute import paths.
3. The formal dataset bootstrap no longer depends on an external private `e:/hangtu3` codebase.
4. The missing public raw inputs can now be recreated directly from a repository script.
5. A smoke test is provided so a new user can validate the repository before running expensive paths.

## 9. Remaining Practical Limits

The project is now reproducible in the practical sense for the fixed formal 100-sample setup, but a few limits still remain:

1. LLM-based paths depend on external API availability and provider behavior.
2. OCR-based paths depend on the local OCR environment and package installation.
3. If the FAA changes or removes historical download URLs in the future, the raw-source bootstrap step may need maintenance.
4. The repository reproduces the committed formal split, not a fresh independent sample-selection study.

## 10. Recommended Verification Order

For a fresh machine, the recommended order is:

1. `python scripts/smoke_test.py`
2. `python scripts/build_dataset_100.py`
3. `python scripts/run_O.py`
4. one path script among `A/B/C/D/E`
5. `python evaluate.py`
6. `python error_analysis.py`

If you only want to inspect the current published result without rerunning everything, start from:

- `results/v2604_100/final_report_100.md`
- `results/v2604_100/evaluation_report.md`
- `results/v2604_100/error_analysis_report.md`
