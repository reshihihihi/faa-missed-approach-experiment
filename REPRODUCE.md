# Reproduction Guide

## Scope

This document describes the practical reproduction assumptions for the current repository state.

It is intentionally lightweight and focuses on the current public repository layout rather than a full environment capture.

## 1. Install Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Current key packages:

- `anthropic`
- `paddleocr`
- `requests`

## 2. Configure Credentials

LLM-based paths expect Anthropic-compatible credentials through environment variables such as:

```bash
ANTHROPIC_API_KEY=...
```

or

```bash
ANTHROPIC_AUTH_TOKEN=...
ANTHROPIC_BASE_URL=...
```

Do not commit secrets to the repository.

## 3. Data Availability

This repository keeps lightweight manifests and reports under version control, but excludes large raw FAA source files by default.

If you want to fully rerun the pipeline, you will need access to the corresponding FAA chart PDFs, rendered chart images, and CIFP files.

Useful metadata files already included:

- `data/v2604_100/sample_manifest_100.json`
- `data/v2604_100/pairs_100.json`
- `data/v2604_100/selection_100.json`
- `data/v2604_100/candidate_pool.json`

## 4. Important Path Assumption

Some current scripts still assume local absolute paths such as:

- `E:/experiment/...`

If you run this repository in another location, update those path settings first.

In particular, inspect:

- `scripts/dataset_config.py`
- `scripts/build_dataset_100.py`
- any script with hard-coded `E:/experiment/...` paths

## 5. Main Execution Entrypoints

Formal path scripts:

- `scripts/run_A.py`
- `scripts/run_B.py`
- `scripts/run_C.py`
- `scripts/run_D.py`
- `scripts/run_E.py`
- `scripts/run_O.py`

Evaluation:

- `evaluate.py`
- `error_analysis.py`

## 6. Example Workflow

```bash
python scripts/run_C.py
python evaluate.py
python error_analysis.py
```

## 7. Current Reference Reports

The current repository already includes generated reports for the formal 100-sample experiment:

- `results/v2604_100/final_report_100.md`
- `results/v2604_100/evaluation_report.md`
- `results/v2604_100/error_analysis_report.md`

These are the main files to consult if you only want to inspect the current experiment results without rerunning everything.

