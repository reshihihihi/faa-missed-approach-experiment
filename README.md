# FAA Missed Approach Extraction Experiment

This repository studies how to extract structured missed-approach information from FAA approach charts and compares five extraction paths on a formal 100-sample dataset.

The current formal dataset is the FAA `2604` cycle. The repository already contains the fixed 100-sample split metadata, the paired structured CIFP procedure data, and the generated evaluation reports. Raw chart PDFs, rendered chart images, and FAA source archives are regenerated locally from public FAA sources.

## Methods

| Path | Description |
|------|-------------|
| `O` | CIFP-derived reference baseline |
| `A` | OCR + rules |
| `B` | OCR + LLM |
| `C` | Image input + multi-question QA + JSON aggregation |
| `D` | Image input + single-pass full JSON extraction |
| `E` | Image input + questionnaire-constrained extraction before final JSON |

## Formal 100-Sample Result

| Path | Scalar F1 | Waypoint F1 |
|------|-----------|-------------|
| A | 0.629 | 0.437 |
| B | 0.588 | 0.647 |
| C | 0.705 | 0.691 |
| D | 0.684 | 0.677 |
| E | 0.687 | 0.688 |

Current takeaways:

- `C` is the strongest overall method on the formal 100-sample run.
- `D` and `E` are strong image-direct baselines with close performance.
- OCR-based paths remain weaker than image-direct paths on this task.

## What Is Versioned In Git

Included:

- `data/v2604_100/sample_manifest_100.json`
- `data/v2604_100/pairs_100.json`
- `data/v2604_100/selection_100.json`
- `data/v2604_100/candidate_pool.json`
- `results/v2604_100/`
- `prompts/`
- `scripts/`
- `docs/`

Not included by default:

- raw FAA chart PDFs
- rendered chart PNGs
- FAA CIFP source archives
- preparation-stage temporary files

This means the repository is lightweight in Git, but still supports end-to-end reruns after downloading the public FAA inputs.

## Repository Layout

- `data/pilot_10/`
  Pilot-only 10-sample materials kept for early workflow history.
- `data/v2604_100/`
  Formal 100-sample dataset metadata and committed pairing data.
- `results/pilot_10/`
  Pilot outputs and pilot reports.
- `results/v2604_100/`
  Formal 100-sample outputs, metrics, error analysis, and final report.
- `scripts/`
  Experiment entrypoints, dataset materialization, and validation scripts.
- `prompts/`
  Prompt files used by the LLM-based paths.
- `docs/`
  Project notes and experiment documentation.

## Environment

Python dependencies are listed in `requirements.txt`:

```bash
pip install -r requirements.txt
```

The main packages are:

- `anthropic`
- `paddleocr`
- `pymupdf`
- `requests`

## Model Configuration

The LLM-based paths use:

- model: `claude-sonnet-4-6`
- temperature: `0`
- client: Anthropic-compatible Python SDK

Supported environment variables:

- `ANTHROPIC_API_KEY`
- `ANTHROPIC_AUTH_TOKEN`
- `ANTHROPIC_BASE_URL`

Do not commit real secrets.

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/reshihihihi/faa-missed-approach-experiment.git
cd faa-missed-approach-experiment
pip install -r requirements.txt
```

### 2. Run the repository smoke test

```bash
python scripts/smoke_test.py
```

### 3. Materialize the public FAA inputs

This downloads the official FAA CIFP archive, the d-TPP metafile, the 100 chart PDFs referenced by the committed manifest, and renders the expected chart PNGs locally.

```bash
python scripts/build_dataset_100.py
```

### 4. Configure credentials for LLM paths

Example PowerShell:

```powershell
$env:ANTHROPIC_AUTH_TOKEN="your_token"
$env:ANTHROPIC_BASE_URL="https://your-compatible-endpoint"
```

### 5. Run the experiment paths

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

### 6. Recompute evaluation and error analysis

```bash
python evaluate.py
python error_analysis.py
```

## Public Data Sources

The formal dataset is built from official FAA public materials for cycle `2604`.

Source families:

- FAA CIFP archive
- FAA d-TPP metafile
- FAA d-TPP chart PDFs

In the current implementation, the exact source endpoints are defined in [scripts/build_dataset_100.py](/E:/experiment/scripts/build_dataset_100.py):

- `CIFP_ZIP_URL`
- `DTPP_XML_URL`
- `DTPP_PDF_BASE`

The repository does not ask readers to search for files manually. Instead, it uses the committed manifest plus these official FAA sources to recreate the missing raw inputs locally.

## How The 100 Samples Were Chosen

The formal 100-sample experiment uses a fixed committed split. Readers do not need to resample the dataset to reproduce the reported experiment, but the selection logic is still preserved for traceability.

The committed files are:

- `data/v2604_100/candidate_pool.json`
- `data/v2604_100/selection_100.json`
- `data/v2604_100/sample_manifest_100.json`
- `data/v2604_100/pairs_100.json`

Selection logic, as reflected by the repository files and scripts:

1. Candidate procedures were drawn from FAA cycle `2604` CIFP data.
2. Only approach procedures relevant to this study were kept, primarily `RNAV`, `LOC`, and `ILS`.
3. Each candidate procedure was matched to an FAA d-TPP approach chart PDF.
4. The missed-approach segment was inspected from the paired CIFP procedure legs to determine attributes such as `holding_required`.
5. A stratified quota was applied over `procedure kind × holding_required`.
6. A per-airport cap of `2` was enforced to reduce over-concentration from a small number of airports.
7. A fixed random seed `2604` was used for the committed formal split.

The current committed quota summary is recorded in [selection_100.json](/E:/experiment/data/v2604_100/selection_100.json):

- `RNAV`, `holding_required=false`: `25`
- `LOC`, `holding_required=false`: `13`
- `ILS`, `holding_required=false`: `2`
- `RNAV`, `holding_required=true`: `35`
- `LOC`, `holding_required=true`: `12`
- `ILS`, `holding_required=true`: `13`

Because the repository preserves the final manifest and pairs file, practical reproduction means rerunning the experiment on this same committed split, not regenerating a brand-new split from scratch.

## Reproducibility Scope

This repository now supports two practical levels of reproduction:

1. Result inspection reproduction
   You can inspect the committed reports and JSON outputs directly from Git without downloading raw FAA assets.
2. End-to-end experiment rerun reproduction
   You can regenerate the missing public raw inputs locally with `python scripts/build_dataset_100.py`, then rerun `O/A/B/C/D/E`, `evaluate.py`, and `error_analysis.py`.

What is fixed and committed:

- the formal 100-sample split
- the sample manifest
- the paired structured CIFP procedure data in `pairs_100.json`
- prompts
- evaluation outputs and reports

What is regenerated locally:

- FAA CIFP archive contents
- chart PDFs
- rendered chart images

## Main Files

- `scripts/build_dataset_100.py`
- `scripts/run_A.py`
- `scripts/run_B.py`
- `scripts/run_C.py`
- `scripts/run_D.py`
- `scripts/run_E.py`
- `scripts/run_O.py`
- `scripts/smoke_test.py`
- `evaluate.py`
- `error_analysis.py`

## Key Reports

- `results/v2604_100/final_report_100.md`
- `results/v2604_100/evaluation_report.md`
- `results/v2604_100/error_analysis_report.md`

## Notes

- The repository no longer requires a hard-coded `E:/experiment` location.
- The formal reproduction flow no longer depends on the external private `e:/hangtu3` codebase.
- Historical pilot files remain in the repository, but the formal experiment is `v2604_100`.
- If you only want the final conclusions, start with `results/v2604_100/final_report_100.md`.

For the exact step-by-step reproduction procedure, see [REPRODUCE.md](REPRODUCE.md).
