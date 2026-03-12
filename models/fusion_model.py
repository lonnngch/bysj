import torch
import torch.nn as nn


class MultiLevelTemporalFusion(nn.Module):
    """
    多层次时序特征融合：
    1) 帧级注意力融合
    2) 片段级平均池化融合
    3) 视频级自适应加权融合
    """

    def __init__(self, feature_dim=768, num_segments=4, hidden_dim=256):
        super().__init__()

        self.feature_dim = feature_dim
        self.num_segments = num_segments

        # 4.3.1 帧级注意力：为每帧计算权重
        self.frame_attn = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, 1)
        )

        # 4.3.3 视频级自适应加权：融合帧级与片段级表示
        self.video_gate = nn.Sequential(
            nn.Linear(feature_dim * 2, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, 2)
        )

    def _segment_pool(self, frame_features):
        """
        4.3.2 片段级平均池化融合
        将时间维切为 num_segments 个片段，每段平均后再全局平均。
        """
        b, t, d = frame_features.shape
        segment_features = []

        for seg_idx in range(self.num_segments):
            start = (seg_idx * t) // self.num_segments
            end = ((seg_idx + 1) * t) // self.num_segments

            # 极短序列时，确保每个片段至少有一个帧索引
            if start == end:
                end = min(start + 1, t)

            cur = frame_features[:, start:end, :]
            segment_features.append(cur.mean(dim=1))

        segment_features = torch.stack(segment_features, dim=1)
        return segment_features.mean(dim=1)

    def forward(self, frame_features):
        """
        frame_features: (B, T, D)
        return: (B, D)
        """
        # 帧级注意力融合
        attn_logits = self.frame_attn(frame_features)  # (B, T, 1)
        attn_weights = torch.softmax(attn_logits, dim=1)
        frame_level = (attn_weights * frame_features).sum(dim=1)  # (B, D)

        # 片段级平均池化融合
        segment_level = self._segment_pool(frame_features)  # (B, D)

        # 视频级自适应加权融合
        fusion_context = torch.cat([frame_level, segment_level], dim=-1)
        gate_logits = self.video_gate(fusion_context)
        gate_weights = torch.softmax(gate_logits, dim=-1)  # (B, 2)

        fused = (
            gate_weights[:, 0:1] * frame_level +
            gate_weights[:, 1:2] * segment_level
        )

        return fused
