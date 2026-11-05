"""
NEU-DET VOC XML -> YOLO TXT 转换 + 训练/验证集划分。
用法：
    uv run python src/app/vision/neu_det_xml2yolo.py
输入：
    NEU-DET/IMAGES/*.jpg
    NEU-DET/ANNOTATIONS/*.xml
输出：
    NEU-DET-yolo/images/{train,val}/*.jpg
    NEU-DET-yolo/labels/{train,val}/*.txt
"""
import os
import random
import shutil
import xml.etree.ElementTree as ET

# ===== 配置 =====
RAW_DIR = os.path.join("ml", "NEU-DET")
OUT_DIR = os.path.join("ml", "NEU-DET-yolo")
IMG_DIR = os.path.join(RAW_DIR, "IMAGES")
XML_DIR = os.path.join(RAW_DIR, "ANNOTATIONS")

# 类别映射：必须和 data.yaml 里的 names 顺序完全一致
CLASSES = [
    "crazing",           # 0
    "inclusion",         # 1
    "patches",           # 2
    "pitted_surface",    # 3
    "rolled-in_scale",   # 4
    "scratches",         # 5
]
CLASS_TO_ID = {name: i for i, name in enumerate(CLASSES)}

# 训练/验证比例
VAL_RATIO = 0.2
RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def convert_box(size, box):
    """VOC 绝对像素坐标 -> YOLO 归一化中心坐标。"""
    dw = 1.0 / size[0]
    dh = 1.0 / size[1]
    x_center = (box[0] + box[1]) / 2.0 * dw
    y_center = (box[2] + box[3]) / 2.0 * dh
    w = (box[1] - box[0]) * dw
    h = (box[3] - box[2]) * dh
    return x_center, y_center, w, h


def parse_xml(xml_path):
    """解析一个 VOC XML，返回 (width, height, [(class_id, xc, yc, w, h), ...])."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    size = root.find("size")
    width = int(size.find("width").text)
    height = int(size.find("height").text)

    boxes = []
    for obj in root.findall("object"):
        name = obj.find("name").text.strip()
        if name not in CLASS_TO_ID:
            continue  # 忽略未知类别
        bnd = obj.find("bndbox")
        xmin = float(bnd.find("xmin").text)
        xmax = float(bnd.find("xmax").text)
        ymin = float(bnd.find("ymin").text)
        ymax = float(bnd.find("ymax").text)

        xc, yc, w, h = convert_box((width, height), (xmin, xmax, ymin, ymax))
        boxes.append((CLASS_TO_ID[name], xc, yc, w, h))
    return width, height, boxes


def main():
    # 路径检查：路径不对时立刻报错，而不是跑到一半才失败
    if not os.path.isdir(IMG_DIR):
        raise FileNotFoundError(f"图片目录不存在: {os.path.abspath(IMG_DIR)}")
    if not os.path.isdir(XML_DIR):
        raise FileNotFoundError(f"标注目录不存在: {os.path.abspath(XML_DIR)}")
    print(f"图片目录: {os.path.abspath(IMG_DIR)}")
    print(f"标注目录: {os.path.abspath(XML_DIR)}")
    
    # 1. 收集所有图片，按 8:2 划分
    all_imgs = [
        f for f in os.listdir(IMG_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    random.shuffle(all_imgs)
    n_val = int(len(all_imgs) * VAL_RATIO)
    val_imgs = set(all_imgs[:n_val])
    train_imgs = set(all_imgs[n_val:])

    # 2. 创建输出目录
    for split in ("train", "val"):
        os.makedirs(os.path.join(OUT_DIR, "images", split), exist_ok=True)
        os.makedirs(os.path.join(OUT_DIR, "labels", split), exist_ok=True)

    # 3. 逐图转换
    found_xml = 0
    for img_name in all_imgs:
        stem = os.path.splitext(img_name)[0]
        xml_path = os.path.join(XML_DIR, stem + ".xml")
        if not os.path.exists(xml_path):
            continue
        found_xml += 1

        split = "val" if img_name in val_imgs else "train"

        # 复制图片
        src_img = os.path.join(IMG_DIR, img_name)
        dst_img = os.path.join(OUT_DIR, "images", split, img_name)
        shutil.copy2(src_img, dst_img)

        # 写 label
        _, _, boxes = parse_xml(xml_path)
        dst_label = os.path.join(OUT_DIR, "labels", split, stem + ".txt")
        with open(dst_label, "w", encoding="utf-8") as f:
            for cls_id, xc, yc, w, h in boxes:
                f.write(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

    print(f"found xml: {found_xml}")
    print(f"train: {len(train_imgs)}  val: {len(val_imgs)}")
    print(f"输出目录: {os.path.abspath(OUT_DIR)}")


if __name__ == "__main__":
    main()