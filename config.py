import torch

VIDEO_DIR = r"F:\毕业论文设计\数据集\KoNViD_1k\KoNViD_1k_videos"
MOS_FILE = r"F:\毕业论文设计\数据集\KoNViD_1k\KoNViD_1k_mos.csv"

FRAME_DIR = r"F:\毕业设计\data\frames"
FEATURE_DIR = r"F:\毕业设计\data\features"
CHECKPOINT_DIR = r"F:\毕业设计\checkpoints"
BEST_MODEL_PATH = r"F:\毕业设计\checkpoints\best_model.pth"

IMG_SIZE = 224
BATCH_SIZE = 4
EPOCHS = 4
LR = 1e-4
VAL_RATIO = 0.2
SEED = 42

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# CNN-based VQA baseline metrics for comparison plot.
# Please replace values with your reproduced/quoted CNN baseline results.
CNN_BASELINE_METRICS = {
    "PLCC": 0.58,
    "SRCC": 0.61,
    "RMSE": 0.58,
    "Loss": 0.34
}