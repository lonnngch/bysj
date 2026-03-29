import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.utils.data import DataLoader, random_split
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


def evaluate(model, loader, loss_fn):
    model.eval()

    total_loss = 0
    preds = []
    gts = []

    with torch.no_grad():
        for frames, score in loader:
            frames = frames.to(config.DEVICE)
            score = score.to(config.DEVICE)

            pred = model(frames)
            loss = loss_fn(pred, score)

            total_loss += loss.item()
            preds.extend(pred.detach().cpu().numpy().flatten())
            gts.extend(score.cpu().numpy().flatten())

    avg_loss = total_loss / len(loader)
    srcc, plcc, rmse = compute_metrics(preds, gts)

    return avg_loss, srcc, plcc, rmse


def plot_method_comparison(our_metrics, cnn_metrics, epoch):
    metric_names = ["PLCC", "SRCC", "RMSE", "Loss"]
    our_values = [
        our_metrics["PLCC"],
        our_metrics["SRCC"],
        our_metrics["RMSE"],
        our_metrics["Loss"]
    ]
    cnn_values = [
        cnn_metrics["PLCC"],
        cnn_metrics["SRCC"],
        cnn_metrics["RMSE"],
        cnn_metrics["Loss"]
    ]

    x = np.arange(len(metric_names))

    plt.figure(figsize=(10, 6))
    plt.plot(x, our_values, marker="o", linewidth=2, label="Our Model (ViT)")
    plt.plot(x, cnn_values, marker="s", linewidth=2, label="CNN-based VQA")

    plt.xticks(x, metric_names)
    plt.title("VQA Metrics Line Comparison")
    plt.ylabel("Metric Value")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.4)

    for i, value in enumerate(our_values):
        plt.text(i, value, f"{value:.4f}", ha="center", va="bottom", fontsize=9)

    for i, value in enumerate(cnn_values):
        plt.text(i, value, f"{value:.4f}", ha="center", va="top", fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(config.CHECKPOINT_DIR, f"metrics_line_comparison_epoch_{epoch+1}.png"))
    plt.close()


def main():
    os.makedirs(config.CHECKPOINT_DIR, exist_ok=True)

    full_dataset = VideoDataset()
    val_size = max(1, int(len(full_dataset) * config.VAL_RATIO))
    train_size = len(full_dataset) - val_size

    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(config.SEED)
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=True,
        num_workers=0  # Windows 必须用 0
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.BATCH_SIZE,
        shuffle=False,
        num_workers=0
    )

    model = ViTFeature().to(config.DEVICE)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.LR
    )

    loss_fn = torch.nn.MSELoss()

    best_val_srcc = -1

    loss_history = []
    best_val_metrics = {
        "PLCC": 0.0,
        "SRCC": 0.0,
        "RMSE": 0.0,
        "Loss": 0.0
    }

    for epoch in range(config.EPOCHS):
        print("\n========== Epoch", epoch + 1, "==========")

        model.train()
        total_loss = 0

        for frames, score in tqdm(train_loader, desc="Training"):
            frames = frames.to(config.DEVICE)
            score = score.to(config.DEVICE)

            pred = model(frames)
            loss = loss_fn(pred, score)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        loss_history.append(avg_loss)

        val_loss, val_srcc, val_plcc, val_rmse = evaluate(model, val_loader, loss_fn)

        print("Train Loss:", avg_loss)
        print("Val Loss:  ", val_loss)
        print("Val SRCC:  ", val_srcc)
        print("Val PLCC:  ", val_plcc)
        print("Val RMSE:  ", val_rmse)

        torch.save(model.state_dict(), os.path.join(config.CHECKPOINT_DIR, "last_model.pth"))

        if val_srcc > best_val_srcc:
            best_val_srcc = val_srcc
            best_val_metrics = {
                "PLCC": val_plcc,
                "SRCC": val_srcc,
                "RMSE": val_rmse,
                "Loss": val_loss
            }
            torch.save(model.state_dict(), config.BEST_MODEL_PATH)
            print("✅ Best model saved!")

        plt.figure()
        plt.plot(loss_history)
        plt.title("Training Loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.savefig(os.path.join(config.CHECKPOINT_DIR, "loss_curve.png"))
        plt.close()

        # 调用时传入 epoch
        plot_method_comparison(
            our_metrics=best_val_metrics,
            cnn_metrics=config.CNN_BASELINE_METRICS,
            epoch=epoch
        )

    print("\n========== Training Finished ==========")
    print("Best Our Model:", best_val_metrics)
    print("CNN Baseline:", config.CNN_BASELINE_METRICS)


if __name__ == "__main__":
    main()