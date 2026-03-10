import torch

VIDEO_DIR = r"F:\毕业论文设计\数据集\KoNViD_1k\KoNViD_1k_videos"
MOS_FILE = r"F:\毕业论文设计\数据集\KoNViD_1k\KoNViD_1k_mos.csv"

FRAME_DIR = r"F:\毕业设计\data\frames"
FEATURE_DIR = r"F:\毕业设计\data\features"

IMG_SIZE = 224
BATCH_SIZE = 4
EPOCHS = 10
LR = 1e-4

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")