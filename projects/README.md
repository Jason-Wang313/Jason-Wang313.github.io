# Robot Learning, 3D Vision, and Diffusion Projects

Four independent projects inspired by ETH Zürich and Stanford coursework. Each guide starts with the question, then gives the commands and explains how to read the outputs.

| Project | What it compares | Guide |
| --- | --- | --- |
| **SO100 recovery** | Extra clean demonstrations vs. targeted DAgger corrections | [Setup and rollout evaluation](so100-recovery.md) |
| **Diffusion obstacle avoidance** | MSE vs. diffusion on the same left- and right-route data | [Training and route comparison](diffusion-avoidance.md) |
| **Handheld 3D reconstruction** | Camera registration and scene coverage at different frame intervals | [Video-to-point-cloud workflow](handheld-reconstruction.md) |
| **Fashion-MNIST DDPM** | Matched samples and inference time at 10, 25, and 50 DDIM steps | [Training and sampling](fashion-mnist-ddpm.md) |

The two SO100 projects share the same MuJoCo course environment and evaluator. The reconstruction uses COLMAP. The Fashion-MNIST project uses PyTorch and shares its diffusion schedule and sampler with the robot policy.

[Technical Writing](https://jason-wang313.github.io/blog/)
