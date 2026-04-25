# B1/B3/B3V3 Pilot Scripts

These scripts are the pilot implementation used to generate the B1/B3/B3V2/B3V3 result package under:

`results/pilot_10/b3v3_region_ocr_20260425/`

They are included for review and reproducibility of the current pilot method. Raw FAA chart images, boxed preview images, OCR caches, and local credentials are intentionally not committed.

## Workspace Root

Most scripts expect a B1-B3 working directory with this layout:

```text
data/pilot10/
outputs/B1_ocr_llm/
outputs/B3_region_ocr_llm/
outputs/B3_region_ocr_llm_v2/
outputs/B3_region_ocr_llm_v3/
targets/canonical_proxy_gt_10/
schemas/missed_approach_leg.schema.json
```

By default, scripts use the repository root as the working root. To run against an external prepared workspace, set:

```powershell
$env:FAA_B1_B3_ROOT = "<path-to-prepared-B1-B3-workspace>"
```

or pass `--root` where supported.

## Main Pilot Flow

```powershell
python scripts\b1_b3_pilot\run_paddleocr_previous.py --root $env:FAA_B1_B3_ROOT --method all
python scripts\b1_b3_pilot\build_b3_candidate_legs.py --root $env:FAA_B1_B3_ROOT
python scripts\b1_b3_pilot\build_b3v3_semantic_candidates.py --root $env:FAA_B1_B3_ROOT
python scripts\b1_b3_pilot\run_llm_extraction.py --root $env:FAA_B1_B3_ROOT --method B3V3 --force
python scripts\b1_b3_pilot\build_b3v3_evidence_trace.py --root $env:FAA_B1_B3_ROOT
python scripts\b1_b3_pilot\score_b1_b3_outputs.py --root $env:FAA_B1_B3_ROOT
python scripts\b1_b3_pilot\score_b1_b3_extended.py --root $env:FAA_B1_B3_ROOT
```

## Validation

```powershell
python scripts\b1_b3_pilot\validate_no_leakage.py --strict-prompt "$env:FAA_B1_B3_ROOT\outputs\B3_region_ocr_llm_v3\prompt_inputs"
python scripts\b1_b3_pilot\validate_bbox_normalization.py "$env:FAA_B1_B3_ROOT\outputs\B3_region_ocr_llm_v3\prompt_inputs"
python scripts\b1_b3_pilot\validate_method_output.py "$env:FAA_B1_B3_ROOT\outputs\B3_region_ocr_llm_v3\method_outputs"
python scripts\b1_b3_pilot\validate_official_schema.py --schema "$env:FAA_B1_B3_ROOT\schemas\missed_approach_leg.schema.json" "$env:FAA_B1_B3_ROOT\outputs\B3_region_ocr_llm_v3\method_outputs"
```

## Credentials

`run_llm_extraction.py` supports Anthropic and OpenAI-compatible providers. It reads credentials from environment variables only:

```text
ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN
OPENAI_API_KEY
OPENAI_BASE_URL optional
```

No credential files are required or committed.
