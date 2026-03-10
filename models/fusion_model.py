import torch
import torch.nn as nn

class FusionModel(nn.Module):

    def __init__(self):

        super().__init__()

        self.fc1 = nn.Linear(256, 128)
        self.fc2 = nn.Linear(128, 1)

    def forward(self, x):

        x = x.mean(dim=1)

        x = torch.relu(self.fc1(x))

        x = self.fc2(x)

        return x.squeeze()