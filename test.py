import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
import config
from dataset.video_dataset import VideoDataset
from models.vit_model import ViTFeature
from utils.metrics import compute_metrics


def main():

    print("========== Video Quality Test ==========")

    # 数据集
    print("Loading dataset...")
    dataset = VideoDataset()
    print("Dataset size:", len(dataset))

    loader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False
    )

    # 模型
    print("Loading model...")
    model = ViTFeature().to(config.DEVICE)

    # 加载权重
    print("Loading checkpoint...")
    ckpt = torch.load(
        config.BEST_MODEL_PATH,
        map_location=config.DEVICE
    )

    model.load_state_dict(ckpt)

    model.eval()
    print("Model loaded successfully")

    preds = []
    gts = []

    print("Start testing...")

    with torch.no_grad():

        for frames, score in tqdm(loader):

            frames = frames.to(config.DEVICE)

            pred = model(frames)

            preds.append(pred.item())
            gts.append(score.item())

    print("Testing finished")

    # 计算指标
    srcc, plcc, rmse = compute_metrics(preds, gts)

    print("========== Test Result ==========")
    print("SRCC:", srcc)
    print("PLCC:", plcc)
    print("RMSE:", rmse)


if __name__ == "__main__":
    main()