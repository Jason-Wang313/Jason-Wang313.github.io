"""Paired SO100 evaluation. Run with HW3 installed and its assets available."""
import argparse
import json
from collections import Counter, deque
from pathlib import Path

import mujoco
import numpy as np
import torch
from hw3.eval_utils import apply_action, check_cube_out_of_bounds, check_success, infer_action_chunk, load_checkpoint
from hw3.sim_env import SO100SimEnv
from so101_gym.constants import ASSETS_DIR


def obstacle_contact(env, obstacle_bodies):
    for c in env.data.contact[:env.data.ncon]:
        a, b = (int(env.model.geom_bodyid[g]) for g in (c.geom1, c.geom2))
        if (a in obstacle_bodies) != (b in obstacle_bodies):
            other = b if a in obstacle_bodies else a
            if other != 0 and c.dist <= 0:
                return True
    return False


def run(checkpoint, episodes, seed, steps, device, repeat_layout):
    torch.manual_seed(seed)
    model, normalizer, _, state_keys, action_keys = load_checkpoint(checkpoint, device)
    env = SO100SimEnv(xml_path=ASSETS_DIR / "so100_transfer_cube_obstacle_ee.xml",
                      render_w=640, render_h=480, use_mocap=True,
                      obstacle_mode="adversarial", seed=seed)
    bodies = set()
    for name in ("obstacle", "upper_obstacle"):
        idx = mujoco.mj_name2id(env.model, mujoco.mjtObj.mjOBJ_BODY, name)
        if idx >= 0:
            bodies.add(idx)
    if not bodies:
        raise RuntimeError("No obstacle bodies found.")
    metrics = []
    try:
        for episode in range(episodes):
            if repeat_layout:
                env.rng = np.random.default_rng(seed)
            torch.manual_seed(seed + episode)
            obs = env.reset()
            obstacle = env.get_obstacle_pos().copy()
            queue = deque()
            path = []
            touched = False
            for _ in range(steps):
                if not queue:
                    queue.extend(infer_action_chunk(model=model, normalizer=normalizer,
                                obs=obs, state_keys=state_keys, device=device))
                apply_action(env, queue.popleft(), action_keys)
                obs = env.step()
                path.append(env.get_ee_pos().copy())
                touched |= obstacle_contact(env, bodies)
                if check_success(env) or check_cube_out_of_bounds(env):
                    break
            path = np.asarray(path)
            # Proxy for approach side: gripper x-offset at closest y crossing.
            crossing = int(np.argmin(np.abs(path[:, 1] - obstacle[1])))
            offset = path[crossing, 0] - obstacle[0]
            route = "left" if offset < -.02 else "right" if offset > .02 else "central"
            metrics.append({"success": bool(check_success(env)), "obstacle_contact": touched,
                            "route_proxy": route, "obstacle_xyz": obstacle.tolist(),
                            "gripper_path": path.tolist()})
    finally:
        env.renderer.close()
    return {"successes": sum(r["success"] for r in metrics),
            "obstacle_contacts": sum(r["obstacle_contact"] for r in metrics),
            "route_proxy_counts": dict(Counter(r["route_proxy"] for r in metrics)),
            "episodes": metrics}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoints", nargs="+", type=Path)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--steps", type=int, default=600)
    parser.add_argument("--seed", type=int, default=5042)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--repeat-layout", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.episodes < 1 or args.steps < 1:
        parser.error("episodes and steps must be positive")
    results = {str(p): run(p, args.episodes, args.seed, args.steps, torch.device(args.device), args.repeat_layout)
               for p in args.checkpoints}
    args.output.write_text(json.dumps({"seed": args.seed, "results": results}, indent=2), encoding="utf-8")
