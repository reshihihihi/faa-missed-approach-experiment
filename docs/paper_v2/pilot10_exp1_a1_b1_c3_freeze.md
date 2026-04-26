# Pilot-10 Exp1 A1/B1/C3 参数冻结方案

## 0. 定位

本文件冻结 `paper_v2_pilot10_exp1_a1_b1_c3` 的 **pilot-only** 运行参数和可继承通用规则。

本 pilot 只用于验证实验组 1 的最小流程是否可行：

```text
完整航图
  -> A1 OCR+Rules
  -> B1 OCR+LLM
  -> C3 image->questionnaire->canonical JSON
  -> parser / validator / scorer / no-leakage check
```

本 pilot 不作为正式论文主结果。如果根据 pilot 结果修改 prompt、parser、schema wrapper、scorer 或 input policy，正式实验必须重新冻结并重跑。

## 1. 继承已有 issue / PR 的冻结要求

本 pilot 继承以下已有 issue / PR 的设计，不在本文件中重新定义这些上位规范。

| 项目 | 继承来源 | 本 pilot 中的用法 |
|---|---|---|
| canonical schema | PR #28 | 使用 leg-level canonical schema |
| C3 questionnaire / structured form | PR #28 | 使用 questionnaire-style 输出并转 canonical JSON |
| Q_terminator vocabulary | PR #28, issue #27 | 使用 24 种 ARINC code + `unknown` |
| field status vocabulary | issue #7, PR #28 | 使用 `present / not_applicable / not_observable / unknown / invalid` |
| proxy target 口径 | issue #3, issue #5, PR #29, PR #32 | target 只作为 scoring proxy，不作为绝对真值 |
| formal300 / practice assets | PR #32 | pilot 样本优先从 formal300 之外的 practice/pilot assets 选取 |
| unknown / not_observable prompt 原则 | issue #20 | B1 / C3 prompt 必须允许拒判 |
| A1 / B1 / C3 方法大类 | issue #11, issue #12, issue #13 | 继承方法方向，本文件冻结本次 pilot 的具体运行边界 |

> 注意：如果 PR #28 / #29 / #32 在本 pilot 运行时仍未合并，本 pilot 必须记录实际使用的 PR head commit。本 pilot 结果不进入正式论文主表；正式 eval 应在 v2 manifest 固化后重跑。

## 2. 通用可继承冻结规则

本节中的规则不只服务 pilot。后续 paper-v2 的实验组 1-7 应默认继承这些规则，除非显式升级版本并记录变更原因。

### 2.1 Schema / scorer 通用规则

所有方法输出必须投影到同一个 canonical schema：

```text
unit: chart / procedure
structure: procedure -> legs -> Q_terminator + Q1-Q5
schema_source: TBD, expected PR #28 commit d2c54172b31184f8c0deb74415f37c239d3e3eca
schema_path: TBD, expected schemas/missed_approach_leg.schema.json
```

字段状态允许值：

```text
present
not_applicable
not_observable
unknown
invalid
```

`Q_terminator` 允许值：

```text
CA, CF, CI, CR, DF, FA, FM, HA, HF, HM, IF, RF,
TF, VA, VD, VI, VM, VR, AF, CD, FC, FD, VC, PI,
unknown
```

pilot 中暂定 scorer 规则：

```text
schema validation failure -> invalid
unparseable model output -> invalid
missing required leg / field -> missing / invalid, not silently dropped
unknown / not_observable must be preserved, not coerced to null
```

如果 pilot 后修改 schema/scorer 口径，必须升级版本，例如：

```text
schema_policy_v0 -> schema_policy_v1
scorer_policy_v0 -> scorer_policy_v1
```

### 2.2 Allowed / forbidden input 通用规则

#### A1: OCR + Rules

Allowed inputs:

```text
full chart image
OCR text generated from the full chart image
OCR bbox / confidence generated from the full chart image
fixed Rules code
```

Forbidden inputs:

```text
canonical target
expected value
gold_ma_prose
evidence provenance
challenge tags
field-to-leg target mapping
Q_terminator answer
human parsed fields
```

#### B1: OCR + LLM

Allowed inputs:

```text
full-chart OCR text
OCR bbox / confidence only if the prompt explicitly declares their use
B1 prompt
```

Forbidden inputs:

```text
chart image
gold_ma_prose
canonical target
expected value
field-to-leg target mapping
evidence provenance
challenge tags
human parsed fields
Q_terminator answer
```

#### C3: image -> questionnaire -> canonical JSON

Allowed inputs:

```text
full chart image
frozen questionnaire prompt / template
```

Forbidden inputs:

```text
OCR text
gold_ma_prose
canonical target
expected value
field-to-leg target mapping
evidence provenance
challenge tags
human parsed fields
Q_terminator answer
```

### 2.3 Prompt 通用规则

所有 LLM/VLM prompt 必须显式允许：

```text
unknown
not_observable
图上看不出
无法判断
```

Prompt 不得强迫模型在无证据时硬选具体值。

每个 prompt 必须记录：

```text
prompt_path
prompt_hash
prompt_source
method_id
run_id
created_at
inherits_issue_20 = true / false
```

如果 prompt 内容发生变化：

```text
must generate a new prompt_hash
must generate a new run_id
must not overwrite previous results
```

### 2.4 Parser repair 通用规则

Allowed repair:

```text
remove markdown code fence
extract the first JSON object
remove explanatory text before/after JSON
normalize field-name casing
normalize unknown / not observable / cannot determine to schema vocabulary
mark invalid according to schema, instead of filling answers
```

Forbidden repair:

```text
modify field values using canonical target
repair JSON using scorer result
manually fill Q_terminator
manually add missing legs
manually fill altitude / fix / turn / hold values
delete failed samples
change wrong answers to unknown
```

Parse failure handling:

```text
keep raw output
record parse_error
mark final output invalid
include invalid output in scorer statistics
never silently drop samples
```

Parser policy version for this pilot:

```text
parser_repair_policy_v0
```

### 2.5 Run manifest / output structure 通用规则

Each run must save:

```text
input_manifest.jsonl
run_manifest.json
raw_outputs/
parsed_json/
final_canonical_json/
prediction.jsonl
validation_report.json
```

`run_manifest.json` must include at least:

```json
{
  "run_id": "TBD",
  "method_id": "A1/B1/C3",
  "experiment_id": "pilot10_exp1_a1_b1_c3",
  "sample_manifest": "TBD",
  "schema_source": "TBD",
  "target_source": "TBD",
  "model_config_hash": "TBD",
  "prompt_hash": "TBD",
  "parser_policy_version": "parser_repair_policy_v0",
  "input_policy_version": "input_policy_v0",
  "output_path": "TBD",
  "created_at": "TBD"
}
```

### 2.6 Rerun policy 通用规则

Allowed reruns:

```text
API timeout
network error
OCR process crash
file read failure
empty model service response
```

Reruns that must not overwrite previous results:

```text
wrong answer
poor score
unsatisfactory prompt
unexpected parser behavior
one method looks disadvantaged
```

If prompt / parser / model / OCR changes:

```text
must create a new run_id
must preserve previous raw_outputs
must record change reason
must not overwrite previous prediction.jsonl
```

## 3. Pilot-specific frozen parameters

本节只服务本次 10 张图试跑，不直接推广到正式 eval。

### 3.1 Pilot run_id

Initial run id:

```text
pilot10_exp1_a1_b1_c3_v0
```

If prompt changes:

```text
pilot10_exp1_a1_b1_c3_v1_prompt_fix
```

If parser changes:

```text
pilot10_exp1_a1_b1_c3_v2_parser_fix
```

### 3.2 Pilot10 sample manifest

Sample source priority:

```text
1. formal300 外的 practice10 / pilot10 assets
2. additionally collected FAA missed approach charts outside formal300
3. formal300 samples only if marked excluded_from_formal_eval = true
```

Each sample record should use this shape:

```json
{
  "chart_id": "TBD",
  "procedure_id": "TBD",
  "split": "pilot10_dev",
  "source_image": "TBD",
  "canonical_target": "TBD",
  "selection_reason": "ordinary / holding / ca_leg / multi_leg / ocr_hard / path_terminator_hard",
  "excluded_from_formal_eval": true,
  "source_ref": "TBD"
}
```

Pilot10 sample manifest path:

```text
benchmark_exports/derived/v2/pilot10_manifest.jsonl
```

### 3.3 Pilot schema / questionnaire / target source

Expected frozen sources for this pilot:

```text
schema_source:
  PR #28
  commit: d2c54172b31184f8c0deb74415f37c239d3e3eca
  path: schemas/missed_approach_leg.schema.json

questionnaire_source:
  PR #28
  commit: d2c54172b31184f8c0deb74415f37c239d3e3eca
  path: prompts/path_e_v2/structured_form_template.txt

target_source:
  PR #32 or practice10 / formal300 target path
  commit: d606b747a1cda86a013df1f145de2a1fa17e176d

cifp_pipeline_provenance:
  PR #29
  commit: 1930aa381955ed1c2001d62dd9dae797d2fddc68
```

If a different commit/path is used, update this section before running the pilot.

### 3.4 Pilot OCR / LLM / VLM parameters

```json
{
  "run_id": "pilot10_exp1_a1_b1_c3_v0",
  "ocr": {
    "applies_to": ["A1", "B1"],
    "engine": "TBD",
    "version": "TBD",
    "settings": "TBD"
  },
  "llm": {
    "applies_to": ["B1"],
    "model": "TBD",
    "temperature": 0,
    "top_p": 1,
    "max_tokens": "TBD"
  },
  "vlm": {
    "applies_to": ["C3"],
    "model": "TBD",
    "temperature": 0,
    "top_p": 1,
    "max_tokens": "TBD",
    "image_resolution_policy": "TBD"
  }
}
```

The pilot should not run until all `TBD` fields required for the selected methods are filled.

### 3.5 Pilot prompt paths and hashes

Recommended prompt paths:

```text
prompts/paper_v2/b1_ocr_to_canonical_pilot10.md
prompts/paper_v2/c3_questionnaire_pilot10.md
```

Prompt manifest shape:

```json
[
  {
    "method_id": "B1",
    "prompt_path": "prompts/paper_v2/b1_ocr_to_canonical_pilot10.md",
    "prompt_hash": "TBD",
    "inherits": ["issue #20 unknown/not_observable instruction"]
  },
  {
    "method_id": "C3",
    "prompt_path": "prompts/paper_v2/c3_questionnaire_pilot10.md",
    "prompt_hash": "TBD",
    "inherits": ["PR #28 structured questionnaire", "issue #20 unknown/not_observable instruction"]
  }
]
```

### 3.6 Pilot output paths

```text
predictions/paper_v2/pilot10_exp1_a1_b1_c3_v0/A1/
predictions/paper_v2/pilot10_exp1_a1_b1_c3_v0/B1/
predictions/paper_v2/pilot10_exp1_a1_b1_c3_v0/C3/

reports/paper_v2/pilot10_exp1_a1_b1_c3_v0/
```

Each method directory should contain:

```text
input_manifest.jsonl
run_manifest.json
raw_outputs/
parsed_json/
final_canonical_json/
prediction.jsonl
validation_report.json
```

Report directory should contain:

```text
pilot10_summary.md
parse_error_report.json
no_leakage_report.json
pilot10_metrics.csv
```

## 4. Pilot success criteria

Pilot success is pipeline stability, not high score.

Success criteria:

```text
10 samples enter A1/B1/C3 runners
all methods produce input_manifest
all methods preserve raw_outputs
all methods produce parsed_json or invalid records
final_canonical_json can enter validator/scorer
parse failures are not silently dropped
no-leakage checks pass
A1/B1/C3 can be summarized in one pilot table
observed issues can be attributed to OCR / prompt / parser / schema / scorer / input packing
```

Not success criteria:

```text
B1 high score
C3 high score
A1 exceeding a threshold
claiming one method is significantly better on pilot10
```

## 5. Pilot to formal freeze promotion rules

If pilot passes, the following can be promoted to formal common policy:

```text
schema/scorer policy
allowed/forbidden input policy
prompt unknown/not_observable policy
parser repair policy
run manifest/output policy
rerun policy
```

The following must not be directly promoted to formal eval:

```text
pilot10 sample IDs
pilot run_id
pilot prompt hash
pilot output paths
pilot result tables
```

If pilot causes changes to any of the following:

```text
schema
prompt
parser
scorer
input policy
```

then formal evaluation must:

```text
bump policy version
record change reason
freeze formal eval configuration again
rerun from frozen formal eval inputs
```

## 6. Summary

This pilot freeze separates reusable paper-v2 common policy from pilot-specific parameters. The common rules are designed to satisfy the experiment plan's requirements for canonical schema, no-leakage, parser handling, run traceability, and rerun discipline. The pilot-specific parameters are only for the 10-chart feasibility run and must not be treated as formal evaluation settings.
