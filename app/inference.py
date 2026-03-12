from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from PIL import Image
from scipy.ndimage import laplace
from torchvision import transforms
from torchvision.io import read_video

import config
from models.vit_model import ViTFeature


class VideoQualityInferenceService:
    def __init__(self, checkpoint_path: str = "checkpoints/best_model.pth") -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self.device = config.DEVICE
        self.transform = transforms.Compose(
            [
                transforms.Resize((config.IMG_SIZE, config.IMG_SIZE)),
                transforms.ToTensor(),
            ]
        )
        self.model = None
        self.engine = "heuristic"
        self._load_model()

    def _load_model(self) -> None:
        if not self.checkpoint_path.exists():
            return

        model = ViTFeature(num_segments=4).to(self.device)
        state = torch.load(self.checkpoint_path, map_location=self.device)
        model.load_state_dict(state)
        model.eval()

        self.model = model
        self.engine = "vit_fusion"

    def _sample_video_frames(self, video_path: str, max_frames: int = 12) -> Tuple[List[np.ndarray], float]:
        frames, _, info = read_video(video_path, pts_unit="sec")
        total = int(frames.shape[0])
        fps = float(info.get("video_fps", 0.0) or 0.0)
        duration = (total / fps) if fps else 0.0

        if total <= 0:
            return [], 0.0

        indexes = np.linspace(0, total - 1, num=min(max_frames, total), dtype=int)
        sampled = [frames[idx].numpy() for idx in indexes]
        return sampled, duration

    def _heuristic_score(self, frames: List[np.ndarray]) -> Tuple[float, float]:
        if not frames:
            return 1.0, 0.0

        sharpness_values = []
        exposure_values = []

        for frame in frames:
            gray = np.dot(frame[..., :3], [0.299, 0.587, 0.114])
            sharpness_values.append(float(laplace(gray).var()))
            exposure_values.append(float(gray.mean()))

        sharpness = float(np.mean(sharpness_values))
        exposure = float(np.mean(exposure_values))

        sharpness_norm = np.clip(sharpness / 500.0, 0.0, 1.0)
        exposure_norm = 1.0 - (abs(exposure - 127.0) / 127.0)
        exposure_norm = np.clip(exposure_norm, 0.0, 1.0)

        score = 1.0 + 4.0 * (0.6 * sharpness_norm + 0.4 * exposure_norm)
        confidence = 0.5 + 0.5 * float(np.std(sharpness_values) < 50)

        return float(np.clip(score, 1.0, 5.0)), float(np.clip(confidence, 0.0, 1.0))

    def _model_score(self, frames: List[np.ndarray]) -> Tuple[float, float]:
        assert self.model is not None

        tensor_frames = []
        for frame in frames:
            img = Image.fromarray(frame.astype(np.uint8))
            tensor_frames.append(self.transform(img))

        if not tensor_frames:
            return 1.0, 0.0

        x = torch.stack(tensor_frames).unsqueeze(0).to(self.device)

        with torch.no_grad():
            pred = self.model(x).item()

        score = float(np.clip(pred, 1.0, 5.0))
        confidence = float(np.clip(0.6 + 0.08 * len(tensor_frames), 0.0, 0.98))
        return score, confidence

    def predict_video(self, video_path: str, filename: str) -> Dict:
        frames, duration = self._sample_video_frames(video_path)

        if self.model is not None and frames:
            score, confidence = self._model_score(frames)
        else:
            score, confidence = self._heuristic_score(frames)

        return {
            "filename": filename,
            "score": round(score, 3),
            "confidence": round(confidence, 3),
            "duration_sec": round(duration, 3),
            "frame_count": len(frames),
            "engine": self.engine,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
