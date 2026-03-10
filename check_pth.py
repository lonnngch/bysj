import torch

ckpt = torch.load(r"F:\毕业设计\checkpoints\best_model.pth", map_location="cpu")

print(type(ckpt))
print(ckpt)