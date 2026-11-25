"""Extract phone-video frames and compare CPU-only sparse COLMAP reconstructions."""
import argparse
import json
import re
import subprocess
from pathlib import Path

import cv2


def invoke(*args):
    proc = subprocess.run([str(a) for a in args], check=True, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout


def cpu_flag(colmap, command, options):
    help_text = invoke(colmap, command, "-h")
    for option in options:
        if option in help_text:
            return [option, "0"]
    raise RuntimeError(f"Could not confirm the CPU option for {command}")


def extract(video, frames, stride, limit):
    stream = cv2.VideoCapture(str(video))
    n = 0
    try:
        for i in range(limit * stride):
            ok, frame = stream.read()
            if not ok:
                break
            if i % stride:
                continue
            h, w = frame.shape[:2]
            scale = min(1, 960 / max(h, w))
            if scale < 1:
                frame = cv2.resize(frame, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
            if not cv2.imwrite(str(frames / f"{i:06d}.jpg"), frame):
                raise OSError("Could not save a video frame")
            n += 1
    finally:
        stream.release()
    return n


def reconstruct(colmap, video, root, stride, limit):
    root.mkdir(parents=True, exist_ok=False)
    images = root / "images"
    images.mkdir()
    n = extract(video, images, stride, limit)
    if n < 2:
        raise ValueError(f"Stride {stride} produced fewer than two images")
    db = root / "database.db"
    models = root / "sparse"
    models.mkdir()
    invoke(colmap, "feature_extractor", "--database_path", db, "--image_path", images,
           "--ImageReader.single_camera", "1", *cpu_flag(colmap, "feature_extractor",
           ("--FeatureExtraction.use_gpu", "--SiftExtraction.use_gpu")))
    invoke(colmap, "sequential_matcher", "--database_path", db,
           *cpu_flag(colmap, "sequential_matcher", ("--FeatureMatching.use_gpu", "--SiftMatching.use_gpu")))
    invoke(colmap, "mapper", "--database_path", db, "--image_path", images, "--output_path", models)
    candidates = []
    for model in sorted(models.iterdir()):
        if not model.is_dir():
            continue
        report = invoke(colmap, "model_analyzer", "--path", model)
        (root / f"model-{model.name}.txt").write_text(report, encoding="utf-8")
        def metric(label):
            match = re.search(label + r":\s+([0-9.]+)", report)
            return float(match[1]) if match else None
        candidates.append({"model": model, "registered": int(metric("Registered images") or 0),
                           "points": int(metric("Points") or 0),
                           "mean_reprojection_error_px": metric("Mean reprojection error")})
    if not candidates:
        return {"stride": stride, "input_frames": n, "registered": 0}
    best = max(candidates, key=lambda x: x["registered"])
    model = best.pop("model")
    invoke(colmap, "model_converter", "--input_path", model, "--output_path", root / "points.ply",
           "--output_type", "PLY")
    return {"stride": stride, "input_frames": n, **best}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("video", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--colmap", default="colmap")
    p.add_argument("--strides", nargs="+", type=int, default=[5, 10, 20])
    p.add_argument("--max-frames", type=int, default=40)
    a = p.parse_args()
    if min(a.strides) < 1 or a.max_frames < 2:
        p.error("Use positive strides and at least two frames")
    results = [reconstruct(a.colmap, a.video.resolve(), a.output / f"stride-{s}", s, a.max_frames)
               for s in a.strides]
    (a.output / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
