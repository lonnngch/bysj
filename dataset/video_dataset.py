import os
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms
from config import FRAME_DIR, MOS_FILE

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])


class VideoDataset(Dataset):

    def __init__(self):

        self.data = pd.read_csv(MOS_FILE)

    def __len__(self):

        return len(self.data)

    def __getitem__(self, idx):

        video_name = str(self.data.iloc[idx, 0])
        mos = float(self.data.iloc[idx, 1])

        frame_folder = os.path.join(FRAME_DIR, video_name)

        frames = []

        for img_name in sorted(os.listdir(frame_folder)):

            img_path = os.path.join(frame_folder, img_name)

            img = Image.open(img_path).convert("RGB")

            img = transform(img)

            frames.append(img)

        frames = torch.stack(frames)

        return frames, torch.tensor([mos], dtype=torch.float32)

if __name__ == "__main__":

    dataset = VideoDataset()

    print("dataset size:", len(dataset))

    frames, mos = dataset[0]

    print("frames shape:", frames.shape)
    print("mos:", mos)