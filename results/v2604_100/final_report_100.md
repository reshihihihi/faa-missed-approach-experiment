# 100样本航图复飞信息抽取实验最终报告

## 1. 实验目标

本实验面向 FAA 进近航图中的 missed approach instruction，目标是从航图中自动抽取结构化复飞信息，并比较不同技术路线的效果。

统一评估的核心字段为：

- `climb_altitude`
- `turn_direction`
- `holding_required`
- `holding_fix`
- `waypoints`

本报告只统计正式的 100 样本实验结果，不包含此前 10 样本的探索性试验。

## 2. 数据与基准

### 2.1 数据来源

本轮实验数据来自 FAA 官方资料：

- FAA d-TPP 航图
- FAA CIFP 程序数据
- 周期版本：`2604`

样本集位于：

- `data/v2604_100/sample_manifest_100.json`
- `data/v2604_100/pairs_100.json`

### 2.2 样本规模与构成

- 总样本数：100
- 对应 100 张唯一航图
- 程序类型前缀分布：
  - `R`: 62
  - `L`: 25
  - `I`: 13
- `holding_required = true`：62
- `holding_required = false`：38

### 2.3 参考基准 O

路径 `O` 不是待比较方案，而是参考基准。其作用是：

- 从 FAA CIFP 中定位对应程序的 missed approach 段
- 将 424 编码内容转换为可核对的结构化 JSON
- 作为各实验方案统一对齐的真值基准

参考输出位于：

- `results/v2604_100/O`

## 3. 实验方案

本轮正式比较的方案共有五种：

### 3.1 路径 A：OCR + 规则抽取

流程为：

- 对航图图像执行 `PaddleOCR`
- 提取 OCR 文本
- 基于规则、正则和字段逻辑进行结构化抽取

这是传统可解释型基线。优点是流程透明，缺点是容易受 OCR 顺序混乱和干扰文本影响。

### 3.2 路径 B：OCR + LLM

流程为：

- 使用与 A 相同的 `PaddleOCR`
- 将 OCR 文本输入大模型
- 由模型输出结构化 JSON

因此，A 与 B 的 OCR 阶段相同，核心差异在于：

- A：OCR 后接规则法
- B：OCR 后接 LLM 语义抽取

### 3.3 路径 C：多轮单问题 QA

这是本轮新增方案。流程为：

- 直接输入航图图像，不走 OCR 文本链路
- 不一次性要求模型输出完整 JSON
- 针对 `raw_instruction`、`climb_altitude`、`turn_direction`、`holding_required`、`holding_fix`、`waypoints` 分别单独提问
- 每轮只回答一个字段
- 最后再汇总为统一 JSON

该方案的设计目的，是检验“多轮单问题问答”是否能降低一次性整包抽取时的过预测与字段串扰。

### 3.4 路径 D：图像直接理解 + 单步 JSON 抽取

流程为：

- 直接输入航图图像
- 由多模态模型整体理解图文内容
- 单轮输出完整结构化 JSON

该方案不依赖先验 OCR 文本，重点考察模型的整体图像理解能力。

### 3.5 路径 E：图像直接理解 + 问卷约束后输出 JSON

流程仍然是图像直读，但提示策略比 D 更强约束：

- 先进行问卷式确认
- 再输出最终 JSON

其目标是增强模型对显式证据的检查，减少直接生成完整 JSON 时的自由发挥。

## 4. 评估方法

评估脚本位于：

- `evaluate.py`

评估结果位于：

- `results/v2604_100/evaluation_report.md`
- `results/v2604_100/all_metrics.json`

### 4.1 Scalar 指标

用于评估单值字段：

- `climb_altitude`
- `turn_direction`
- `holding_required`
- `holding_fix`

对这些字段统计 Precision、Recall、F1，并汇总为 `Scalar F1`。

### 4.2 Waypoint 指标

用于评估 `waypoints` 集合字段，统计：

- Waypoint Precision
- Waypoint Recall
- Waypoint F1
- Mean Waypoint Jaccard
- Waypoint Exact Rate

其中 `Waypoint F1` 反映 waypoint 集合整体抽取能力，`Mean Waypoint Jaccard` 反映集合重叠程度，`Waypoint Exact Rate` 反映整组航路点是否完全正确。

## 5. 实验结果

### 5.1 总体结果

100 样本正式实验总体结果如下：

| Path | OutputCoverage | Scalar F1 | Waypoint F1 | MeanWaypointJaccard | WaypointExactRate |
|------|----------------|-----------|-------------|---------------------|-------------------|
| A | 1.000 | 0.629 | 0.437 | 0.391 | 0.350 |
| B | 1.000 | 0.588 | 0.647 | 0.513 | 0.480 |
| C | 1.000 | 0.705 | 0.691 | 0.555 | 0.550 |
| D | 1.000 | 0.684 | 0.677 | 0.545 | 0.530 |
| E | 1.000 | 0.687 | 0.688 | 0.545 | 0.540 |

可以看到：

- 五种方案都实现了 `OutputCoverage = 1.000`
- `C` 在 `Scalar F1` 和 `Waypoint F1` 上均为最高
- `D` 与 `E` 非常接近
- `A` 明显弱于其余方案
- `B` 在 waypoint 上明显优于 A，但 scalar 综合表现不如 C/D/E

### 5.2 字段级结果

#### Path A

| Field | Precision | Recall | F1 |
|-------|-----------|--------|----|
| climb_altitude | 0.596 | 0.815 | 0.688 |
| turn_direction | 0.700 | 0.700 | 0.700 |
| holding_required | 0.560 | 0.560 | 0.560 |
| holding_fix | 0.521 | 0.597 | 0.556 |
| waypoints | 0.357 | 0.563 | 0.437 |

#### Path B

| Field | Precision | Recall | F1 |
|-------|-----------|--------|----|
| climb_altitude | 0.616 | 0.938 | 0.744 |
| turn_direction | 0.310 | 0.310 | 0.310 |
| holding_required | 0.640 | 0.640 | 0.640 |
| holding_fix | 0.582 | 0.919 | 0.712 |
| waypoints | 0.496 | 0.930 | 0.647 |

#### Path C

| Field | Precision | Recall | F1 |
|-------|-----------|--------|----|
| climb_altitude | 0.650 | 1.000 | 0.788 |
| turn_direction | 0.680 | 0.680 | 0.680 |
| holding_required | 0.650 | 0.650 | 0.650 |
| holding_fix | 0.594 | 0.919 | 0.722 |
| waypoints | 0.545 | 0.944 | 0.691 |

#### Path D

| Field | Precision | Recall | F1 |
|-------|-----------|--------|----|
| climb_altitude | 0.650 | 1.000 | 0.788 |
| turn_direction | 0.610 | 0.610 | 0.610 |
| holding_required | 0.640 | 0.640 | 0.640 |
| holding_fix | 0.592 | 0.935 | 0.725 |
| waypoints | 0.528 | 0.944 | 0.677 |

#### Path E

| Field | Precision | Recall | F1 |
|-------|-----------|--------|----|
| climb_altitude | 0.626 | 0.954 | 0.756 |
| turn_direction | 0.687 | 0.680 | 0.683 |
| holding_required | 0.626 | 0.620 | 0.623 |
| holding_fix | 0.571 | 0.903 | 0.700 |
| waypoints | 0.545 | 0.930 | 0.688 |

## 6. 结果分析

### 6.1 综合结论

本轮 100 样本实验下，综合表现排序可概括为：

`C > E ≈ D > B > A`

更准确地说：

- `C` 是当前综合表现最好的方案
- `D` 与 `E` 都很强，但没有超过 `C`
- `B` 说明 LLM 对 OCR 文本有明显增益，但 OCR 链路本身仍是瓶颈
- `A` 适合做传统可解释基线，不适合作为最优主方案

### 6.2 A 的特点

`A` 的优势在于：

- 可解释性强
- 规则链路明确
- 易于定位错误来源

但其上限明显受限于：

- OCR 文本顺序不稳定
- 航图中存在大量非复飞说明文本干扰
- 规则对复杂图文布局适应性不足

因此，A 更适合作为基线或辅助检查路径，而不是主力方案。

### 6.3 B 的特点

`B` 与 `A` 共用同一 OCR，因此能较清晰地反映“规则法”和“LLM 文本抽取”的差异。

结果表明：

- `B` 的 `waypoints` 与 `holding_fix` 明显优于 `A`
- 说明在相同 OCR 输入下，LLM 的语义归纳能力确实优于规则法
- 但 `turn_direction` 很弱，说明 OCR 文本链路在方向信息上仍容易破碎、歧义或被污染

因此，B 比 A 更强，但仍受 OCR 上游质量制约。

### 6.4 C 的特点

`C` 是本轮新增的关键方案，结果说明：

- 多轮单问题 QA 确实有效
- 与 D/E 同样属于“图像直读”路线，但在输出组织方式上更细粒度
- 它在 `Scalar F1` 与 `Waypoint F1` 上都取得了最高值

从实验结果看，C 的优势主要来自：

- 降低了一次性生成完整 JSON 时的字段耦合
- 减少了单轮输出中多个字段互相污染的情况
- 对 waypoint、holding_fix、climb_altitude 这类字段更稳定

这说明把任务拆成多个单问题，是当前数据集下有效的方法改进，而不是仅仅换了提问措辞。

### 6.5 D 与 E 的特点

`D` 和 `E` 都属于图像直接理解方案，整体表现很接近，说明：

- 图像直读路线整体上优于 OCR 路线
- 多模态模型能够更好地利用航图中的布局、箭头、局部标注和邻近关系

其中：

- `D` 更接近“直接看图后一次性输出”
- `E` 在此基础上增加问卷与输出约束

但在本轮 100 样本上，E 相比 D 的优势很小，没有形成明显拉开。说明“先问卷后 JSON”这类输出控制是有帮助的，但增益没有 C 的“多轮拆字段”那样明显。

### 6.6 waypoint 结果的意义

`waypoints` 是区分不同方案能力最关键的维度之一。

本轮结果：

- A：0.437
- B：0.647
- C：0.691
- D：0.677
- E：0.688

这说明：

- 规则法对 waypoint 集合抽取最不稳定
- OCR + LLM 已能显著提升 waypoint 抽取
- 图像直读方案整体更稳
- 多轮单问题 QA 在 waypoint 上进一步取得了最优表现

## 7. 主要错误类型

错误分类结果位于：

- `results/v2604_100/error_analysis_report.md`
- `results/v2604_100/error_analysis.json`

### 7.1 A 的主要错误

- `holding_required:false_hold`
- `climb_altitude:spurious_prediction`
- `waypoints:spurious_only`
- `holding_fix:spurious_prediction`
- `turn_direction:hallucinated_turn`

说明 A 的主要问题是把非复飞说明误当成复飞信息，并进一步连带产生 holding、fix 和 waypoint 的串联误判。

### 7.2 B 的主要错误

- `waypoints:spurious_only`
- `turn_direction:wrong_direction`
- `holding_fix:spurious_prediction`
- `holding_required:false_hold`
- `climb_altitude:spurious_prediction`

说明 B 虽然比 A 更会做语义归纳，但 OCR 文本中的方向信息仍然很容易误导模型。

### 7.3 C 的主要错误

- `waypoints:spurious_only`
- `climb_altitude:spurious_prediction`
- `holding_fix:spurious_prediction`
- `holding_required:false_hold`
- `turn_direction:hallucinated_turn`

C 的错误模式与 D/E 有相似性，但总体数量更少，尤其在 waypoint 杂音错误上更受控。

### 7.4 D 的主要错误

- `waypoints:spurious_only`
- `holding_fix:spurious_prediction`
- `holding_required:false_hold`
- `climb_altitude:spurious_prediction`
- `turn_direction:hallucinated_turn`

说明图像直读虽然整体更强，但仍会在“图上存在多个相邻导航元素”时出现多抓、误抓。

### 7.5 E 的主要错误

- `waypoints:spurious_only`
- `holding_fix:spurious_prediction`
- `holding_required:false_hold`
- `climb_altitude:spurious_prediction`
- `turn_direction:hallucinated_turn`

E 与 D 的错误类型接近，说明它主要是在同一路线上做输出控制优化，而不是改变底层识别模式。

## 8. 最终结论

本轮 100 样本正式实验可以得出以下结论：

1. OCR + 规则法可以作为基线，但整体能力明显受限。
2. 在相同 OCR 输入下，LLM 抽取优于规则法，证明语义抽取是有效增益。
3. 图像直读路线整体优于 OCR 路线，说明航图任务中版面和图像结构信息非常重要。
4. 新增的多轮单问题 QA 方案 `C` 在本轮实验中取得了最佳综合表现，是当前最值得继续推进的主方案。
5. D/E 仍然是强有力对照组，尤其适合用于说明“图像直读”相对 OCR 路线的优势。
6. 当前最主要的剩余问题仍是过预测，包括：
   - 把非目标 waypoint 混入结果
   - 把不需要的 holding 误判为需要
   - 在 holding_fix 上产生附带性误抓

因此，下一步优化应继续围绕“抑制过预测、提升字段边界判断、加强主复飞路径约束”展开，而不是再回到更复杂的 OCR 规则堆叠。
