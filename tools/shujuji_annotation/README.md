# 复飞航图多人协同标注工作区

本目录提供 FAA missed approach 复飞实验的人工校准数据集与多人协同标注平台。平台采用浏览器前端 + Node.js 服务端结构，所有运行时读写均限定在本目录下的相对路径中。

## 目录结构

- `annotation_platform/`：标注网页与 Node.js 服务端代码。
- `datasets/practice10/`：10 张练习航图，用于熟悉标注流程，不进入正式统计。
- `datasets/formal300/`：300 张正式航图、预标注、PR #28 canonical target 与 manifest。
- `docs/`：人工标注教程、多人协同说明、字段对应规则。
- `scripts/`：数据集构建和预标注生成脚本。
- `config/`：CIFP 最大集合与样本构建相关配置。

## 启动方式

在本目录运行：

```bat
启动标注平台.bat
```

或手动运行：

```powershell
cd tools\shujuji_annotation\annotation_platform
node server.js
```

启动后访问：

- 练习集：`http://127.0.0.1:8787/practice/`
- 正式集：`http://127.0.0.1:8787/formal/`
- 局域网协作：`http://主机IP:8787/formal/`

## 数据保存

正式标注按标注人分开保存，避免多人互相覆盖：

- 暂存：`datasets/formal300/annotations/drafts/by_annotator/<annotator>/<chart_id>.json`
- 暂存快照：`datasets/formal300/annotations/drafts/snapshots/<chart_id>/...json`
- 正式提交：`datasets/formal300/annotations/by_annotator/<annotator>/<chart_id>.json`
- 正式提交快照：`datasets/formal300/annotations/submissions/<chart_id>/...json`

浏览器端不会显示服务器本机绝对路径，接口响应也会对内部路径做脱敏处理。

## 提交内容说明

本次提交包含平台运行所需的代码、300 张正式航图 PNG、练习集、预标注 JSON、canonical target JSON、字段教程和协同标注文档。PDF 原件、调试预览、历史重置备份和运行日志不纳入版本库。
