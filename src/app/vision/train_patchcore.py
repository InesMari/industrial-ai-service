import os
# 设置镜像（建议保留，避免后续下载模型时网络问题）
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HOME'] = r'E:\IndustryAI\cache'

from anomalib.data import MVTecAD
from anomalib.models import Patchcore
from anomalib.engine import Engine

def main():
    # 1. 数据：锁定 transistor 类别
    datamodule = MVTecAD(
        root="./datasets/MVTecAD",
        category="transistor",
        train_batch_size=32,
        num_workers=0,  # 关键修改：Windows 下设为 0
    )

    # 2. 模型
    model = Patchcore(
        backbone="wide_resnet50_2",
        layers=["layer2", "layer3"],
        coreset_sampling_ratio=0.1,
    )

    # 3. 训练 + 评估
    engine = Engine()
    engine.fit(model=model, datamodule=datamodule)
    results = engine.test(model=model, datamodule=datamodule)
    print("测试指标:", results)

if __name__ == '__main__':
    main()