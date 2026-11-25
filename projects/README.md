# Robot learning and 3D vision course projects

## 1. SO100 recovery with DAgger

Start with a disposable checkout of the [ETH Robot Learning course](https://github.com/mees-robot-learning-course/ethz-course-2026) at commit `2e089e97d84968182c1ffa2e1bc8177530feb6fe`. Install the HW3 dependencies and configure the teleoperation key map as described in its README. From the HW3 directory, install the single-cube policy extensions:

```sh
python /path/to/projects/install_so100.py . --epochs 25
python -m pip install -e .
```

Use the course's `scripts/record_teleop_demos.py` to record a baseline set and a separate clean supplement. Keep the raw Zarr recordings in separate directories. Convert baseline recordings with:

```sh
python scripts/compute_actions.py --datasets-dir raw/baseline --action-space ee --output datasets/baseline.zarr
python scripts/train.py --zarr datasets/baseline.zarr --policy obstacle --chunk-size 8 --state-keys state_ee_xyz state_gripper "state_cube[:3]" state_obstacle --action-keys action_ee_xyz action_gripper
```

Copy the checkpoint to a unique filename before starting the next run. Record corrective demonstrations with the course's `scripts/dagger_eval.py --checkpoint <baseline-checkpoint> --output-dir raw/corrections`. Let the baseline act and take over with the configured record key in states that need correction. Place the extras for each condition in its own raw directory, then process each independently:

```sh
python scripts/compute_actions.py --datasets-dir raw/extra-clean --action-space ee --output datasets/extra-clean.zarr
python scripts/compute_actions.py --datasets-dir raw/corrections --action-space ee --output datasets/extra-corrections.zarr
python /path/to/projects/match_demos.py datasets/baseline.zarr datasets/extra-clean.zarr datasets/extra-corrections.zarr datasets/matched --chunk-size 8
```

Train once on `datasets/matched/clean.zarr` and once on `datasets/matched/corrections.zarr`, using the same training arguments as baseline. Rename each resulting checkpoint before the next run. The matcher equalizes the number of full extra action windows, rather than teleoperator time or number of episodes. Keep an independent seed for rollout evaluation and do not use those rollouts for collection or model selection.

```sh
python /path/to/projects/evaluate_so100.py checkpoints/baseline.pt checkpoints/clean.pt checkpoints/corrections.pt --seed 5042 --output recovery.json
```

The evaluator records binary task success, observed obstacle contact at control-step boundaries, and gripper paths. It uses the same seeded layout sequence for each checkpoint. Short contacts between control steps may be missed. MuJoCo still needs a rendering context in this pinned environment even when the evaluator never displays a window.

## 2. Diffusion policies for obstacle avoidance

Collect both left and right approaches to the **same** obstacle configurations using the same teleoperation workflow. Convert those demonstrations to one processed store and use it for both policies. Run the training command above twice on that store, replacing the policy with `obstacle` for the MSE baseline and `diffusion` for the conditional diffusion policy. Keep the same seed, feature list, action representation, and eight-step horizon. Preserve both checkpoint files.

Run the evaluator on both checkpoints. It logs rollout-level success, contact, and a coarse left/right/central proxy measured near the obstacle, plus complete gripper trajectories. Inspect the trajectories, especially centrally classified and failed runs. For a multimodality follow-up, pass `--repeat-layout` to reset the same layout with a different Torch seed on each episode and compare successful routes. Across-layout route counts alone cannot establish bimodality at a fixed observation. The policy uses deterministic DDIM per initial noise draw and fresh noise for each action chunk.

## 3. Handheld-video 3D reconstruction

Install COLMAP and `opencv-python`. Use a short video with visible texture, sideways camera motion, and overlap between views. Then run:

```sh
python reconstruct.py phone.mp4 runs/desk --strides 5 10 20 --max-frames 40
```

The script decodes frames, downsizes them, runs CPU feature extraction and sequential matching, and registers cameras using COLMAP's sparse mapper. It saves a PLY point cloud, the native camera poses in the sparse model, and a JSON summary of image registration, point count, and mean reprojection error. Use a new output directory for each comparison. For a fair stride comparison, trim the source clip to a duration covered by all three settings. A low reprojection error on a small registered subset is weak evidence of a strong reconstruction.

## 4. Fashion-MNIST DDPM

Install compatible PyTorch and torchvision builds for your platform. The training command downloads Fashion-MNIST the first time.

```sh
python fashion_ddpm.py train --output runs/fashion --device cpu
python fashion_ddpm.py compare --output runs/fashion --checkpoint runs/fashion/denoiser.pt --device cpu
```

The default is a compact 28 × 28 denoiser trained on a seeded 6,000-image subset. The comparison uses one checkpoint and the same batch of initial noise for 10, 25, and 50 DDIM steps. It writes a matched image grid and median inference time over three repeats per budget. Inspect image quality from the grid. The script does not produce a quantitative quality score. Use `--limit 0` for the full dataset or `--device cuda` if a GPU is available later.
