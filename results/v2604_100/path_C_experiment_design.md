# 新路径 C 试验方案设计

> 状态说明
> - 本文件是新路径 `C` 的设计阶段文档。
> - 当前 `C` 已完成正式落地、编号迁移与 100 样本运行。
> - 其中“拟调整”“建议”“尚未完成”等表述保留为设计过程记录，不代表当前最终状态。
> - 当前正式方法口径以 `docs/实验方案.md` 与 `final_report_100.md` 为准。

## 1. 背景与目的

在当前 100 样本正式实验中，已完成方案的编号口径拟调整为：

- `A`：OCR + 规则抽取
- `B`：OCR + LLM
- `C`：新增，多轮单问题 QA
- `D`：原图像直接理解单次整体抽取（原 `C`）
- `E`：原问卷约束图像整体抽取（原 `D`）
- `O`：CIFP 参考基准

现有结果表明，图像直接理解路线 `D/E` 整体优于 `A/B`，但主要错误仍集中在“过预测”：

- `waypoints:spurious_only`
- `holding_fix:spurious_prediction`
- `holding_required:false_hold`
- `turn_direction:hallucinated_turn`

因此，新增路径 `C` 的核心目的不是简单追求更高总分，而是检验如下方法学问题：

**将 missed approach 信息抽取拆分为多个单字段问答任务，是否能够降低整体抽取中的过预测，并提升字段级稳定性。**

## 2. 新 C 的方法定位

新路径 `C` 定义为：

**图像直接输入 + 多轮单问题 QA + 最终汇总 JSON**

与现有方案的差异如下：

- 相比 `A`
  - `A` 依赖 OCR 文本和规则
  - `C` 不依赖 OCR，不依赖规则，直接看图逐字段问答

- 相比 `B`
  - `B` 是 OCR 文本输入 + 单次结构化抽取
  - `C` 是图像输入 + 多轮字段级问答

- 相比 `D`
  - `D` 是图像输入 + 单次整体 JSON 抽取
  - `C` 是图像输入 + 多轮单字段问答
  - 核心差异在于“整体式抽取”与“分解式抽取”

- 相比 `E`
  - `E` 是图像输入 + 先问卷后整体 JSON
  - `C` 是图像输入 + 逐字段独立 QA
  - `E` 是整体级约束，`C` 是字段级分解

因此，新 `C` 的方法学定位可以概括为：

**通过字段级分解问答，减少单次整体抽取中字段之间的相互污染，从而抑制过预测。**

## 3. 输入、输出与对齐要求

### 3.1 输入

新 `C` 必须与现有 100 样本实验保持严格对齐：

- 数据集：`E:/experiment/data/v2604_100`
- 样本清单：[sample_manifest_100.json](E:/experiment/data/v2604_100/sample_manifest_100.json)
- 样本配对：[pairs_100.json](E:/experiment/data/v2604_100/pairs_100.json)
- 参考基准：[O](E:/experiment/results/v2604_100/O)

输入模态固定为：

- 航图图像
- 不输入 OCR 文本
- 不输入 CIFP 文本
- 不输入额外外部知识

这样可以确保与 `D/E` 的比较仅体现“抽取策略差异”，而不是“输入信息差异”。

### 3.2 输出

虽然中间采用多轮 QA，但最终输出必须与现有实验统一 schema 对齐：

```json
{
  "raw_instruction": "...",
  "climb_altitude": 3000,
  "waypoints": ["MUDRE"],
  "turn_direction": "NONE",
  "holding_required": true,
  "holding_fix": "MUDRE",
  "initial_track": null,
  "turn_trigger": null,
  "holding_details": null
}
```

第一版 `C` 建议仅对当前正式评估使用的字段做重点设计：

- `raw_instruction`
- `climb_altitude`
- `turn_direction`
- `holding_required`
- `holding_fix`
- `waypoints`

其余字段第一版统一设置为：

- `initial_track = null`
- `turn_trigger = null`
- `holding_details = null`

## 4. 核心试验思路

新 `C` 采用“先定位，再逐字段提问，再汇总”的流程。

关键原则如下：

### 原则 1：字段独立

每个关键字段通过独立问题单独预测，而不是一次性让模型输出整份结构化结果。

目的：

- 降低字段之间的连带误判
- 减少“先误判有 hold，再顺带编出 holding_fix 和 waypoints”的现象

### 原则 2：与现有评估完全兼容

新 `C` 不能改变数据、参考基准和评估口径，只改变抽取范式。

### 原则 3：优先检验是否减少过预测

重点观察是否降低以下错误：

- `holding_required:false_hold`
- `holding_fix:spurious_prediction`
- `waypoints:spurious_only`
- `turn_direction:hallucinated_turn`

## 5. 推荐的问答设计

建议新 `C` 第一版采用 6 个问题。

### Q1：定位并提取 `raw_instruction`

目标：

- 找到图中的 `MISSED APPROACH` 指令
- 返回原文文本

期望输出：

- 字符串
- 看不清时返回 `unknown`

### Q2：提取 `climb_altitude`

目标：

- 仅判断目标爬升高度

期望输出：

- 整数
- 或 `unknown`

### Q3：提取 `turn_direction`

目标：

- 仅判断是否明确存在 `LEFT / RIGHT / NONE / unknown`

特别要求：

- `NONE` 表示明确没有 left/right
- `unknown` 表示看不清或无法确定

这一步尤其重要，因为 `turn_direction` 是当前方案中最受图形信息和提示方式影响的字段之一。

### Q4：提取 `holding_required`

目标：

- 判断复飞中是否明确包含 holding pattern 或 hold instruction

期望输出：

- `true`
- `false`
- `unknown`

### Q5：提取 `holding_fix`

目标：

- 如果 holding 存在，识别其 fix 名称

期望输出：

- 大写 fix 名
- `null`
- `unknown`

建议逻辑：

- 若 `Q4 != true`，可在程序侧直接赋值 `null`
- 不一定强制额外调用模型

### Q6：提取 `waypoints`

目标：

- 列出 missed approach 中明确出现的 waypoint / fix 名称

期望输出：

- JSON 数组

## 6. 推荐的交互模式

建议新 `C` 第一版采用：

**独立单题模式（推荐正式版）**

即每个问题都只给：

- 同一张航图图像
- 对应问题提示

不携带前一题答案作为上下文。

优点：

- 字段之间互不污染
- 最能体现“字段级 QA”与“整体式抽取”的方法差异
- 更适合作为正式对照实验

缺点：

- 调用次数更多
- 不能利用上一题的中间结果

不建议第一版就采用强级联模式，否则会引入新的误差传播机制，削弱方法对照的清晰性。

## 7. 输出文件设计

为便于评估与后续误差分析，建议新 `C` 输出两类文件。

### 7.1 最终结果

目录：

- `E:/experiment/results/v2604_100/C`

每个样本输出：

- `<sid>.json`

### 7.2 中间 QA 记录

建议同时保存：

- `<sid>_qa.json`

内容建议包括：

- 每一问的 prompt
- 每一问的原始回答
- 解析后的字段值

这样后续可以分析：

- 哪一问最容易出错
- 哪一问最容易输出 `unknown`
- 多轮 QA 是在哪个字段上带来收益或损失

## 8. 评估方式

新 `C` 必须完全复用现有 100 样本评估体系：

- 参考基准：路径 `O`
- 评估脚本：[evaluate.py](E:/experiment/evaluate.py)
- 错误分析脚本：[error_analysis.py](E:/experiment/error_analysis.py)

核心指标保持不变：

- `Scalar F1`
- `Waypoint F1`
- 各字段 Precision / Recall / F1
- 错误类型分析

重点比较问题：

1. `C` 相比 `D/E`，是否降低过预测
2. `C` 是否提升 `turn_direction` 的稳定性
3. `C` 是否提升 `holding_fix` 的 precision
4. `C` 是否在降低过预测的同时带来 recall 损失

## 9. 研究假设

建议在正式实验中明确以下假设：

### 假设 1

多轮单问题 QA 能降低以下错误：

- `holding_required:false_hold`
- `holding_fix:spurious_prediction`
- `waypoints:spurious_only`

### 假设 2

多轮单问题 QA 可能提升字段 precision，但可能降低 recall。

### 假设 3

新 `C` 不一定全面优于 `D/E`，但更可能表现为“更保守、更稳定”。

## 10. 与编号迁移相关的实施要求

由于后续将正式采用新编号口径，实施新 `C` 时必须同步考虑命名迁移。

目标命名体系应为：

- `run_A.py`
- `run_B.py`
- `run_C.py`：新 QA 方案
- `run_D.py`：原 `C`
- `run_E.py`：原 `D`

对应 prompt 也应同步迁移为：

- `path_c_*`：新 QA 方案
- `path_d_*`：原 `C`
- `path_e_*`：原 `D`

在新 `C` 尚未完成前，不建议强行改动历史结果目录中的旧 `C/D` 文件内容；但正式落地前必须在脚本、prompt、评估口径三层统一编号。

## 11. 推荐实施顺序

建议按以下顺序推进：

1. 确认本方案设计
2. 设计 6 个问题的英文 prompt 模板
3. 设计 `run_C.py` 的调用与汇总逻辑
4. 调整编号体系，为新 `C` 预留正式位置
5. 跑通少量样本试运行
6. 运行完整 100 样本
7. 使用统一评估脚本对比 `A/B/C/D/E`

## 12. 结论

新路径 `C` 的最佳定位不是“再做一个和 `D/E` 类似的整体抽取方案”，而是：

**在相同图像输入条件下，引入字段级分解式问答机制，作为对整体式抽取路线的正式方法对照。**

这样设计的优势在于：

- 与现有方案差异清晰
- 能直接回应当前实验中“过预测”这一主要问题
- 与现有 100 样本、统一 JSON schema 和评估脚本完全兼容

该方案适合作为下一阶段正式新增实验路径。
