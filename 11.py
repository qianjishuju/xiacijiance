import torch
from nets.model.Labs.labs import Labs  # 根据你的实际导入路径修改

# 定义模型和加载权重
model = Labs(num_classes=2, backbone="hgnetv2l", downsample_factor=16, pretrained=True, header="aspp", img_sz=[512, 512])
model_path = '/贴胶训训练成功/best.pth'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 打印模型的 state_dict，查看缺失的键
print("Model state_dict keys:", model.state_dict().keys())

# 加载权重文件并捕获可能的错误
try:
    model.load_state_dict(torch.load(model_path, map_location=device))
    print("Model loaded successfully.")
except RuntimeError as e:
    print(f"Error loading model state_dict: {e}")
