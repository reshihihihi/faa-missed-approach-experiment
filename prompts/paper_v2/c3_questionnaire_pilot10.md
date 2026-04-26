# C3 Pilot Prompt: Full Chart Image to Questionnaire-Structured Canonical JSON

Scope: `pilot10_exp1_a1_b1_c3_v0`

You are given one FAA approach chart image. Fill the missed-approach questionnaire and return canonical JSON according to the paper-v2 schema.

Use only the chart image and this questionnaire prompt. Do not use OCR text, gold text, canonical targets, evidence labels, challenge tags, or expected values.

If a field cannot be determined from the chart, use `unknown`. If a field is not applicable to the leg, use `not_applicable`. If a field is not observable from the chart evidence, use `not_observable`. Do not guess when evidence is missing.

Return only JSON. Do not include markdown fences or explanation.

## Questionnaire

TBD: paste or reference the frozen PR #28 structured questionnaire template once schema source is pinned.

## Image input

{{CHART_IMAGE}}
