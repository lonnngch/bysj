import os
import torch
import numpy as np
from torchvision import models, transforms
from PIL import Image
from tqdm import tqdm
import config

model = models.resnet18(pretrained=True)
model = torch.nn.Sequential(*list(model.children())[:-1])
model.to(config.DEVICE)
model.eval()

transform = transforms.Compose([
    transforms.ToTensor()
])

def extract():

    os.makedirs(config.FEATURE_DIR, exist_ok=True)

    videos = os.listdir(config.FRAME_DIR)

    for vid in tqdm(videos):

        frame_dir = os.path.join(config.FRAME_DIR, vid)

        frames = sorted(os.listdir(frame_dir))

        features = []

        for f in frames:

            img = Image.open(os.path.join(frame_dir, f))

            img = transform(img).unsqueeze(0).to(config.DEVICE)

            with torch.no_grad():
                feat = model(img)

            feat = feat.view(-1).cpu().numpy()

            features.append(feat)

        features = np.array(features)

        np.save(
            os.path.join(config.FEATURE_DIR, vid + ".npy"),
            features
        )

if __name__ == "__main__":
    extract()