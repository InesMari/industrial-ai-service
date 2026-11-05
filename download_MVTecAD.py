from anomalib.data import MVTecAD

datamodule = MVTecAD(
    root="./datasets/MVTecAD",
    category="transistor",
)

# 关键：这行才会真正触发下载
datamodule.prepare_data()
print("数据准备完成")