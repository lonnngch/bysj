import torch
from torch.utils.data import DataLoader
import config
from dataset.video_dataset import VideoDataset
from models.vit_model import ViTFeature
from utils.metrics import compute_metrics


def main():

    dataset = VideoDataset()

    loader = DataLoader(dataset, batch_size=1, shuffle=False)

    model = ViTFeature().to(config.DEVICE)

    # 加载模型
    ckpt = torch.load(
        r"F:\毕业设计\checkpoints\best_model.pth",
        map_location=config.DEVICE
    )

    model.load_state_dict(ckpt)

    model.eval()

    preds = []
    gts = []

    with torch.no_grad():

        for frames, score in loader:

            frames = frames.to(config.DEVICE)

            pred = model(frames)

            preds.append(pred.item())
            gts.append(score.item())

    srcc, plcc, rmse = compute_metrics(preds, gts)

    print("SRCC:", srcc)
    print("PLCC:", plcc)
    print("RMSE:", rmse)


if __name__ == "__main__":
    main()