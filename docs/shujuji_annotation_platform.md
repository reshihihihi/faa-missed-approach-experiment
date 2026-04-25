# 复飞航图 300 张标注平台提交说明

本次提交将 `tools/shujuji_annotation` 作为独立的标注工作区加入仓库，用于支持复飞航图数据集的多人协同人工校准。

## 包含内容

- `tools/shujuji_annotation/annotation_platform`：浏览器前端和 Node.js 服务端。
- `tools/shujuji_annotation/datasets/formal300`：300 张正式航图 PNG、manifest、预标注、canonical targets。
- `tools/shujuji_annotation/datasets/practice10`：10 张练习航图和对应练习数据。
- `tools/shujuji_annotation/docs`：人工标注教程、字段对应说明、协同标注说明。
- `tools/shujuji_annotation/scripts`：数据集构建和预标注生成脚本。

## 路径约束

提交前已将数据和代码中的本机绝对路径改为相对路径。平台运行时以 `tools/shujuji_annotation` 为工作区根目录，服务端接口不会向浏览器暴露服务器本机保存路径。

## 不包含内容

PDF 原件、调试预览、运行日志和历史重置备份不纳入版本库。正式标注产生的草稿和提交结果由运行时写入 `datasets/formal300/annotations`。
