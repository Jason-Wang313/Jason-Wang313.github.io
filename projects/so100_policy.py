"""Action chunk policies compatible with the ETH HW3 policy loader."""
import torch
from torch import nn
from torch.nn import functional as F

from hw3.portfolio_diffusion import add_noise, ddim, schedule


def mlp(inputs, outputs, width, depth):
    layers = []
    for _ in range(depth):
        layers.extend((nn.Linear(inputs, width), nn.SiLU()))
        inputs = width
    return nn.Sequential(*layers, nn.Linear(inputs, outputs))


class ObstaclePolicy(nn.Module):
    def __init__(self, state_dim, action_dim, chunk_size, d_model=128, depth=2):
        super().__init__()
        self.action_dim = action_dim
        self.chunk_size = chunk_size
        self.network = mlp(state_dim, action_dim * chunk_size, d_model, depth)

    def sample_actions(self, state):
        return self.network(state).reshape(len(state), self.chunk_size, self.action_dim)

    def compute_loss(self, state, action_chunk):
        return F.mse_loss(self.sample_actions(state), action_chunk)


class DiffusionPolicy(ObstaclePolicy):
    def __init__(self, state_dim, action_dim, chunk_size, d_model=128, depth=2):
        super().__init__(state_dim, action_dim, chunk_size, d_model, depth)
        flat = action_dim * chunk_size
        self.network = mlp(state_dim + flat + 1, flat, d_model, depth)
        self.register_buffer("alpha_bar", schedule())

    def predict_noise(self, state, noisy_actions, timestep):
        time = timestep[:, None].to(state.dtype) / (len(self.alpha_bar) - 1)
        inputs = torch.cat((state, noisy_actions.flatten(1), time), dim=1)
        return self.network(inputs).reshape_as(noisy_actions)

    def compute_loss(self, state, action_chunk):
        timestep = torch.randint(len(self.alpha_bar), (len(state),), device=state.device)
        noise = torch.randn_like(action_chunk)
        noisy = add_noise(action_chunk, noise, timestep, self.alpha_bar)
        return F.mse_loss(self.predict_noise(state, noisy, timestep), noise)

    def sample_actions(self, state):
        noise = state.new_empty((len(state), self.chunk_size, self.action_dim)).normal_()
        return ddim(lambda x, t: self.predict_noise(state, x, t), noise, self.alpha_bar, 12, 5)


def build_policy(policy_type, *, state_dim, action_dim, chunk_size, d_model=128, depth=2):
    cls = {"obstacle": ObstaclePolicy, "diffusion": DiffusionPolicy}[policy_type]
    return cls(state_dim, action_dim, chunk_size, d_model, depth)
