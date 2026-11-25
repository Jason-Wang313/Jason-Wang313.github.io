"""Write two processed Zarr datasets with matched extra full action windows."""
import argparse
from pathlib import Path

import numpy as np
import zarr


def episode_ends(group):
    return np.asarray(group["meta"]["episode_ends"][:], dtype=np.int64)


def windows(group, chunk):
    lengths = np.diff(np.r_[0, episode_ends(group)])
    return int(np.maximum(lengths - chunk + 1, 0).sum())


def match(base, extra, output, budget, chunk):
    spans = []
    start = 0
    for end in episode_ends(extra):
        count = min(max(int(end) - start - chunk + 1, 0), budget)
        if count:
            spans.append((start, start + count + chunk - 1))
            budget -= count
        start = int(end)
        if budget == 0:
            break
    if not spans or budget:
        raise ValueError("Insufficient usable demonstration windows.")
    if output.exists():
        raise FileExistsError(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    original_keys = set(base["data"].array_keys())
    if original_keys != set(extra["data"].array_keys()):
        raise ValueError("Processed data keys do not match.")
    combined = zarr.open_group(str(output), mode="w")
    data = combined.create_group("data")
    for key in sorted(original_keys):
        arr = extra["data"][key]
        data.create_array(key, data=np.concatenate([base["data"][key][:],
                          *(arr[start:end] for start, end in spans)], axis=0))
    ends = episode_ends(base)
    new_ends = ends[-1] + np.cumsum([end-start for start, end in spans])
    combined.create_group("meta").create_array("episode_ends", data=np.r_[ends, new_ends])
    combined.attrs.update(dict(base.attrs))
    combined.attrs["num_dagger_episodes"] = 0
    return int(new_ends[-1])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("baseline")
    p.add_argument("extra_clean")
    p.add_argument("extra_corrections")
    p.add_argument("output", type=Path)
    p.add_argument("--chunk-size", type=int, default=8)
    a = p.parse_args()
    if a.chunk_size < 1:
        p.error("--chunk-size must be positive")
    base, clean, corrections = (zarr.open_group(path, mode="r") for path in
                                (a.baseline, a.extra_clean, a.extra_corrections))
    budget = min(windows(clean, a.chunk_size), windows(corrections, a.chunk_size))
    if budget < 1:
        p.error("Each supplementary dataset needs at least one full action window")
    for name, extra in [("clean", clean), ("corrections", corrections)]:
        print(name, match(base, extra, a.output / (name + ".zarr"), budget, a.chunk_size))
    print(f"Matched {budget} additional training windows per condition.")
