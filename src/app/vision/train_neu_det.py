from ultralytics import YOLO

# 从头加载 YOLOv8n 预训练权重
model = YOLO("yolov8n.pt")

results = model.train(
    data="src/app/vision/neu_det_data.yaml",
    epochs=50,
    imgsz=320,
    batch=16,
    device="cpu",          # 没有 GPU 改成 "cpu"
    workers=0,         # Windows 下设为 0 更稳定
    project="runs/detect",
    name="neu_det",
    exist_ok=True,
)