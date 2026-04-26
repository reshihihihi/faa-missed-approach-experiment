# B1 Pilot Prompt: OCR Text to Canonical Missed Approach JSON

Scope: `pilot10_exp1_a1_b1_c3_v0`

You are given OCR text extracted from one FAA approach chart. Your task is to extract the missed-approach procedure into the project canonical JSON schema.

Use only the OCR text provided in the input. Do not assume access to the chart image, canonical target, gold text, evidence labels, challenge tags, or expected values.

If a field cannot be determined from the OCR text, use `unknown`. If the requested field is not applicable to the leg, use `not_applicable`. If the field is not observable from the provided input, use `not_observable`. Do not guess when evidence is missing.

Return only JSON. Do not include markdown fences or explanation.

## Required output shape

TBD: replace with the exact schema excerpt or reference once the pilot schema source is pinned.

## Input

OCR text:

```text
{{OCR_TEXT}}
```
