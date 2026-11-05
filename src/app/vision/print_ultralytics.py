from ultralytics import YOLO

model = YOLO("runs/detect/runs/detect/neu_det/weights/best.pt")
metrics = model.val(data="src/app/vision/neu_det_data.yaml")

print("mAP@0.5:", metrics.box.map50)
print("mAP@0.5:0.95:", metrics.box.map)
print("Precision:", metrics.box.mp)
print("Recall:", metrics.box.mr)