import torch
import torch.nn as nn
from torchvision.models import vit_b_16, ViT_B_16_Weights

from models.fusion_model import MultiLevelTemporalFusion
class ViTFeature(nn.Module):

    def __init__(self, num_segments=4):

        super().__init__()

        # 加载预训练ViT
        self.vit = vit_b_16(weights=ViT_B_16_Weights.DEFAULT)
        # 去掉原分类头
        self.vit.heads = nn.Identity()
        # 多层次时序融合
        self.temporal_fusion = MultiLevelTemporalFusion(
            feature_dim=768,
            num_segments=num_segments,
            hidden_dim=256
        )
        # 视频质量回归
        self.regressor = nn.Sequential(
            nn.Linear(768, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(p=0.2),
            nn.Linear(256, 1)
        )
    def forward(self, x):
        # x shape: (batch, frames, 3, 224, 224)
        b, t, c, h, w = x.shape
        x = x.view(b * t, c, h, w)
        features = self.vit(x)
        features = features.view(b, t, -1)
        # 多层次时序融合
        features = self.temporal_fusion(features)
        score = self.regressor(features)
        return score
