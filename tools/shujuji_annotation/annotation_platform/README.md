# 标注平台说明

这是复飞航图人工校准用的本地 Web 平台。它用于查看自动预标注框、核对 PR #28 canonical 字段、补充或调整人工框，并把校准结果保存为可追溯的 annotation JSON。

## 启动

从 `tools/shujuji_annotation` 目录运行：

```powershell
cd annotation_platform
node server.js
```

默认端口为 `8787`。也可以通过环境变量覆盖：

```powershell
$env:PORT=8788
node server.js
```

## 入口

- `/practice/`：10 张练习航图。
- `/formal/`：300 张正式航图。
- `/`：入口页。

## 平台读取的数据

服务端以 `tools/shujuji_annotation` 为工作区根目录，读取以下相对路径：

- `datasets/practice10/manifest.json`
- `datasets/formal300/manifest.json`
- `datasets/<dataset>/images/*.png`
- `datasets/<dataset>/prelabels/*.json`
- `datasets/<dataset>/targets/*.json`

## 平台保存的数据

保存路径同样位于 `datasets/<dataset>/annotations/` 下：

- 草稿：`drafts/by_annotator/<annotator>/<chart_id>.json`
- 草稿快照：`drafts/snapshots/<chart_id>/<timestamp>__<annotator>.json`
- 正式提交：`by_annotator/<annotator>/<chart_id>.json`
- 正式提交快照：`submissions/<chart_id>/<timestamp>__<annotator>.json`

正式集会检查领取状态；只有领取该航图的标注人才能暂存或提交。
