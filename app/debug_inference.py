# app/debug_inference.py
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict
import time

logger = logging.getLogger(__name__)


class DebugInferenceService:
    def __init__(self, checkpoint_path: str = "checkpoints/best_model.pth") -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.engine = "debug"
        logger.info(f"使用调试推理服务, 引擎: {self.engine}")

    def predict_video(self, video_path: str, filename: str) -> Dict:
        """调试用的预测函数"""
        logger.info(f"调试推理: {video_path}")

        # 检查文件是否存在
        if not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        # 获取文件信息
        file_size = Path(video_path).stat().st_size
        logger.info(f"文件大小: {file_size} 字节 ({file_size / 1024 / 1024:.2f} MB)")

        # 模拟处理时间
        time.sleep(1)
        logger.info("模拟处理完成")

        # 返回模拟数据
        return {
            "filename": filename,
            "score": 4.2,
            "confidence": 0.85,
            "duration_sec": 10.5,
            "frame_count": 12,
            "engine": self.engine,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }