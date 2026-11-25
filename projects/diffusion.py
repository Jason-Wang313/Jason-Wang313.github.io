"""Shared cosine noise schedule and deterministic DDIM sampler."""
import math

import torch


def schedule(steps=100):
    time = torch.linspace(0, 1, steps + 1)
    curve = torch.cos((time + 0.008) / 1.008 * math.pi / 2).square()
    beta = (1 - curve[1:] / curve[:-1]).clamp(0.00001, 0.999)
    return (1 - beta).cumprod(0)


def add_noise(clean, noise, timestep, alpha_bar):
    shape = (-1,) + (1,) * (clean.ndim - 1)
    alpha = alpha_bar[timestep].reshape(shape)
    return alpha.sqrt() * clean + (1 - alpha).sqrt() * noise


@torch.no_grad()
def ddim(predict_noise, x, alpha_bar, steps, clip_clean=None):
    if not 1 <= steps <= len(alpha_bar):
        raise ValueError("Sampling steps must fit the training schedule.")
    times = torch.linspace(len(alpha_bar) - 1, 0, steps).round().long().tolist()
    for i, current in enumerate(times):
        t = torch.full((len(x),), current, device=x.device, dtype=torch.long)
        noise = predict_noise(x, t)
        alpha = alpha_bar[current]
        clean = (x - (1 - alpha).sqrt() * noise) / alpha.sqrt()
        if clip_clean is not None:
            clean = clean.clamp(-clip_clean, clip_clean)
            noise = (x - alpha.sqrt() * clean) / (1 - alpha).sqrt()
        if i + 1 == len(times):
            return clean
        following = alpha_bar[times[i + 1]]
        x = following.sqrt() * clean + (1 - following).sqrt() * noise
