import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader
from tqdm import tqdm
from scipy.stats import spearmanr, pearsonr

import config
from dataset.video_dataset import VideoDataset
from models.vit_model import ViTFeature


def compute_metrics(preds, gts):

    preds = np.array(preds)
    gts = np.array(gts)

    srcc = spearmanr(preds, gts)[0]
    plcc = pearsonr(preds, gts)[0]
    rmse = np.sqrt(((preds - gts) ** 2).mean())

    return srcc, plcc, rmse


def main():

    os.makedirs("checkpoints", exist_ok=True)

    dataset = VideoDataset()

    loader = DataLoader(
        dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=4
    )

    model = ViTFeature().to(config.DEVICE)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.LR
    )

    loss_fn = torch.nn.MSELoss()

    best_srcc = -1

    loss_history = []

    for epoch in range(config.EPOCHS):

        print("\nEpoch", epoch + 1)

        total_loss = 0

        preds = []
        gts = []

        for frames, score in tqdm(loader):

            frames = frames.to(config.DEVICE)
            score = score.to(config.DEVICE)

            pred = model(frames)

            loss = loss_fn(pred, score)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            preds.extend(pred.detach().cpu().numpy().flatten())
            gts.extend(score.cpu().numpy().flatten())

        avg_loss = total_loss / len(loader)

        srcc, plcc, rmse = compute_metrics(preds, gts)

        loss_history.append(avg_loss)

        print("Loss:", avg_loss)
        print("SRCC:", srcc)
        print("PLCC:", plcc)
        print("RMSE:", rmse)

        # 保存最新模型
        torch.save(
            model.state_dict(),
            "checkpoints/last_model.pth"
        )

        # 保存最佳模型
        if srcc > best_srcc:

            best_srcc = srcc

            torch.save(
                model.state_dict(),
                "checkpoints/best_model.pth"
            )

            print("Best model saved!")

    # 画 Loss 曲线
    plt.figure()

    plt.plot(loss_history)

    plt.title("Training Loss")

    plt.xlabel("Epoch")

    plt.ylabel("Loss")

    plt.savefig("checkpoints/loss_curve.png")

    print("Training finished.")


if __name__ == "__main__":
    main()