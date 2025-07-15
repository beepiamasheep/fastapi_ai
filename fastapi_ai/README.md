# FastAPI_AI 项目

本项目整合了 MinIO 对象存储操作和基于 TFLite 的 YOLOv8 目标检测功能。

## 项目结构
```
AIInference.py       # 实现 YOLOv8 TFLite 模型的推理逻辑
coco8.yaml           # COCO8 数据集的配置文件
mian.py              # 包含 WebSocket 等相关功能代码
minio_tool.py        # 实现 MinIO 对象存储的操作
records/             # 录制文件本地存储文件夹
yolov8n_full_integer_quant.tflite  # YOLOv8 量化后的 TFLite 模型文件
```
---

## 启动设置

提前配置main.py中fastapi的ip、ai推理、minio相关设置

```
python main.py
```

