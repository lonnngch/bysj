# check_model.py
import torch
from pathlib import Path

model_path = Path("checkpoints/best_model.pth")
print(f"模型文件存在: {model_path.exists()}")
if model_path.exists():
    print(f"文件大小: {model_path.stat().st_size} 字节")

    try:
        # 尝试加载模型
        state = torch.load(model_path, map_location='cpu')
        print(f"模型加载成功")
        print(f"状态字典类型: {type(state)}")
        if isinstance(state, dict):
            print(f"键: {list(state.keys())}")
    except Exception as e:
        print(f"模型加载失败: {e}")