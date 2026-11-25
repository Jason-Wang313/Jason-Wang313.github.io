"""Train a compact Fashion-MNIST DDPM and compare fixed-noise DDIM budgets."""
import argparse
import json
import time
from pathlib import Path

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms, utils

from diffusion import add_noise, ddim, schedule


class Denoiser(nn.Module):
    def __init__(self):
        super().__init__()
        self.time_embedding = nn.Embedding(100, 32)
        self.encode = nn.Conv2d(1, 32, 3, padding=1)
        self.down = nn.Conv2d(32, 32, 4, stride=2, padding=1)
        self.middle = nn.Conv2d(32, 32, 3, padding=1)
        self.up = nn.ConvTranspose2d(32, 32, 4, stride=2, padding=1)
        self.output = nn.Conv2d(64, 1, 3, padding=1)

    def forward(self, images, timestep):
        high = F.silu(self.encode(images))
        low = self.down(high) + self.time_embedding(timestep)[:, :, None, None]
        decoded = F.silu(self.up(F.silu(self.middle(F.silu(low)))))
        return self.output(torch.cat((decoded, high), dim=1))


def train(args, device):
    dataset = datasets.FashionMNIST(args.data, train=True, download=True,
        transform=transforms.Compose([transforms.ToTensor(), transforms.Normalize((.5,), (.5,))]))
    if args.limit:
        dataset = Subset(dataset, torch.randperm(len(dataset))[:args.limit].tolist())
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
    model = Denoiser().to(device)
    alpha = schedule().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-4)
    for epoch in range(args.epochs):
        total = 0.
        for clean, _ in loader:
            clean = clean.to(device)
            t = torch.randint(len(alpha), (len(clean),), device=device)
            noise = torch.randn_like(clean)
            loss = F.mse_loss(model(add_noise(clean, noise, t, alpha), t), noise)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total += loss.item() * len(clean)
        print(f"Epoch {epoch+1}: {total/len(dataset):.4f}")
    torch.save(model.state_dict(), args.output / "denoiser.pt")


@torch.no_grad()
def compare(args, device):
    model = Denoiser().to(device)
    model.load_state_dict(torch.load(args.checkpoint, map_location=device, weights_only=True))
    model.eval()
    alpha = schedule().to(device)
    rng = torch.Generator(device=device).manual_seed(args.seed)
    starting_noise = torch.randn((16, 1, 28, 28), generator=rng, device=device)
    def sync():
        if device.type == "cuda":
            torch.cuda.synchronize(device)
    ddim(model, starting_noise.clone(), alpha, 10, 1)
    samples, timings = [], {}
    for n in (10, 25, 50):
        durations = []
        for _ in range(3):
            x = starting_noise.clone()
            sync()
            start = time.perf_counter()
            result = ddim(model, x, alpha, n, 1)
            sync()
            durations.append(time.perf_counter() - start)
        timings[n] = sorted(durations)[1]
        samples.append(result.cpu().add(1).div(2))
    utils.save_image(torch.cat(samples), args.output / "ddim-10-25-50.png", nrow=16)
    (args.output / "timings.json").write_text(json.dumps({
        "device":str(device), "seed":args.seed, "batch_size":16,
        "median_seconds_by_steps":timings,
        "image_rows":[10,25,50]}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["train","compare"])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--limit", type=int, default=6000)
    parser.add_argument("--seed", type=int, default=77)
    args = parser.parse_args()
    if args.epochs < 1 or args.limit < 0:
        parser.error("Use positive epochs and a nonnegative data limit.")
    if args.mode == "compare" and args.checkpoint is None:
        parser.error("compare requires --checkpoint")
    torch.manual_seed(args.seed)
    args.output.mkdir(parents=True, exist_ok=True)
    (train if args.mode == "train" else compare)(args, torch.device(args.device))
