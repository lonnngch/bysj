import torch
import torch.nn as nn
from torchvision.models import vit_b_16, ViT_B_16_Weights


class ViTFeature(nn.Module):

    def __init__(self):

        super().__init__()

        # 加载预训练ViT
        self.vit = vit_b_16(weights=ViT_B_16_Weights.DEFAULT)

        # 去掉原分类头
        self.vit.heads = nn.Identity()

        # 视频质量回归
        self.regressor = nn.Linear(768, 1)

    def forward(self, x):

        # x shape: (batch, frames, 3, 224, 224)
        b, t, c, h, w = x.shape

        x = x.view(b * t, c, h, w)

        features = self.vit(x)

        features = features.view(b, t, -1)

        # 平均池化
        features = torch.mean(features, dim=1)

        score = self.regressor(features)

        return score