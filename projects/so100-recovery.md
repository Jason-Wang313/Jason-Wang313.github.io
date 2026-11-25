# Recovery-aware imitation learning on SO100

[All projects](README.md) · [Robot Learning essay](https://jason-wang313.github.io/blog/robot-learning.html) · [Dataset matcher](match_demos.py) · [Evaluator](evaluate_so100.py)

Does a robot learn more from extra demonstrations of a successful run, or from corrections collected when its own policy goes off course? This comparison gives both variants the same number of additional action windows.
<img src="../blog/cme296-2.gif" alt="Illustration of a robot gripper approaching a cube" width="620">

*Illustration of a robot gripper approaching a cube.*

## Set up the SO100 environment

Start with a disposable checkout of the [ETH Robot Learning course](https://github.com/mees-robot-learning-course/ethz-course-2026) at commit `2e089e97d84968182c1ffa2e1bc8177530feb6fe`. Install the HW3 dependencies and configure the teleoperation key map as described in its README. From the HW3 directory, install the single-cube policy extensions:

```sh
python /path/to/projects/install_so100.py . --epochs 25
python -m pip install -e .
```

## Train a baseline

Use the course's `scripts/record_teleop_demos.py` to record a baseline set and a separate clean supplement. Keep the raw Zarr recordings in separate directories. Convert baseline recordings with:

```sh
python scripts/compute_actions.py --datasets-dir raw/baseline --action-space ee --output datasets/baseline.zarr
python scripts/train.py --zarr datasets/baseline.zarr --policy obstacle --chunk-size 8 --state-keys state_ee_xyz state_gripper "state_cube[:3]" state_obstacle --action-keys action_ee_xyz action_gripper
```

## Collect and match the extra demonstrations

Copy the checkpoint to a unique filename before starting the next run. Record corrective demonstrations with the course's `scripts/dagger_eval.py --checkpoint <baseline-checkpoint> --output-dir raw/corrections`. Let the baseline act and take over with the configured record key in states that need correction. Place the extras for each condition in its own raw directory, then process each independently:

```sh
python scripts/compute_actions.py --datasets-dir raw/extra-clean --action-space ee --output datasets/extra-clean.zarr
python scripts/compute_actions.py --datasets-dir raw/corrections --action-space ee --output datasets/extra-corrections.zarr
python /path/to/projects/match_demos.py datasets/baseline.zarr datasets/extra-clean.zarr datasets/extra-corrections.zarr datasets/matched --chunk-size 8
```

## Train and evaluate the two variants

Train once on `datasets/matched/clean.zarr` and once on `datasets/matched/corrections.zarr`, using the same training arguments as baseline. Rename each resulting checkpoint before the next run. The matcher equalizes the number of full extra action windows, rather than teleoperator time or number of episodes. Keep an independent seed for rollout evaluation and do not use those rollouts for collection or model selection.

```sh
python /path/to/projects/evaluate_so100.py checkpoints/baseline.pt checkpoints/clean.pt checkpoints/corrections.pt --seed 5042 --output recovery.json
```

## Read the rollout report

The evaluator records binary task success, observed obstacle contact at control-step boundaries, and gripper paths. It uses the same seeded layout sequence for each checkpoint. Short contacts between control steps may be missed. MuJoCo still needs a rendering context in this pinned environment even when the evaluator never displays a window.
