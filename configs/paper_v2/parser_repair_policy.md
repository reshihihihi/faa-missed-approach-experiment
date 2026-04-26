# Parser Repair Policy v0

Scope: `pilot10_exp1_a1_b1_c3_v0` and future paper-v2 runs unless superseded.

## Allowed repair

- Remove markdown code fences.
- Extract the first JSON object from surrounding explanatory text.
- Remove explanatory text before or after JSON.
- Normalize field-name casing where the mapping is unambiguous.
- Normalize `unknown`, `not observable`, `cannot determine`, and equivalent phrases to the schema vocabulary.
- Mark missing or malformed fields as `invalid` according to the schema, instead of filling answers.

## Forbidden repair

- Do not modify field values using canonical targets.
- Do not use scorer results to repair predictions.
- Do not manually fill `Q_terminator`.
- Do not manually add missing legs.
- Do not manually fill altitude, fix, turn, course/radial, or hold values.
- Do not delete failed samples.
- Do not convert wrong answers to `unknown` after scoring.

## Parse failure handling

- Preserve raw output.
- Record `parse_error`.
- Mark final output as `invalid`.
- Include invalid outputs in scorer statistics.
- Never silently drop samples.
