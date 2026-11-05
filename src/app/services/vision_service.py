import numpy as np
import cv2
from ultralytics import YOLO

class VisionService:
    def __init__(self, weight_path: str = "runs/detect/neu_det/weights/best.pt"):
        self.model = YOLO(weight_path)

    def detect(self, image_bytes: bytes, conf: float = 0.25) -> list[dict]:
        arr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        results = self.model(img, conf=conf, verbose=False)
        out = []
        for r in results:
            for box in r.boxes:
                out.append({
                    "class": self.model.names[int(box.cls[0])],
                    "confidence": round(float(box.conf[0]), 3),
                    "bbox": [round(v, 1) for v in box.xyxy[0].tolist()],
                })
        return out