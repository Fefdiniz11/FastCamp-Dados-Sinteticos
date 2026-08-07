"""Avalia o modelo BoardVision no conjunto de teste e salva exemplos visuais."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import yaml
from PIL import Image, ImageDraw, ImageFont
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset"
RESULTS_DIR = ROOT / "results"
MODEL_PATH = ROOT / "models" / "best.pt"
CLASS_NAMES = ["dado", "peao", "ficha"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--device", default="auto")
    return parser.parse_args()


def select_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.cuda.is_available():
        return "0"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def write_runtime_yaml() -> Path:
    config = {
        "path": str(DATASET_DIR),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": dict(enumerate(CLASS_NAMES)),
    }
    output = RESULTS_DIR / "data_local.yaml"
    output.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return output


def as_float_list(values: object) -> list[float]:
    if values is None:
        return []
    return [float(value) for value in np.asarray(values).reshape(-1)]


def make_prediction_grid(prediction_dir: Path, output: Path, limit: int) -> None:
    candidates = sorted(prediction_dir.glob("*.png")) + sorted(prediction_dir.glob("*.jpg"))
    images = candidates[:limit]
    if not images:
        return

    thumb_size = 416
    cols = min(4, len(images))
    rows = (len(images) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * thumb_size, rows * (thumb_size + 34)), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)

    for index, path in enumerate(images):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_size, thumb_size))
        x = (index % cols) * thumb_size
        y = (index // cols) * (thumb_size + 34)
        canvas.paste(image, (x, y))
        draw.text((x + 8, y + thumb_size + 7), path.stem, fill="#1f2937", font=font)
    canvas.save(output, quality=95)


def main() -> None:
    args = parse_args()
    device = select_device(args.device)
    data_yaml = write_runtime_yaml()
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Treine o modelo antes da avaliação: {MODEL_PATH}")

    model = YOLO(str(MODEL_PATH))
    metrics = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        workers=0,
        plots=False,
        project=str(RESULTS_DIR),
        name="boardvision_test_metrics",
        exist_ok=True,
        verbose=True,
    )

    # Segunda passagem apenas para gerar uma matriz de confusão legível no
    # limiar usado nas predições, sem alterar as métricas AP oficiais acima.
    model.val(
        data=str(data_yaml),
        split="test",
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        workers=0,
        conf=0.25,
        plots=True,
        project=str(RESULTS_DIR),
        name="boardvision_test",
        exist_ok=True,
        verbose=False,
    )

    per_class_precision = as_float_list(getattr(metrics.box, "p", None))
    per_class_recall = as_float_list(getattr(metrics.box, "r", None))
    per_class_ap50 = as_float_list(getattr(metrics.box, "ap50", None))
    per_class_maps = as_float_list(getattr(metrics.box, "maps", None))
    per_class = {}
    for index, name in enumerate(CLASS_NAMES):
        per_class[name] = {
            "precision": per_class_precision[index] if index < len(per_class_precision) else None,
            "recall": per_class_recall[index] if index < len(per_class_recall) else None,
            "mAP50": per_class_ap50[index] if index < len(per_class_ap50) else None,
            "mAP50_95": per_class_maps[index] if index < len(per_class_maps) else None,
        }

    report = {
        "project": "BoardVision",
        "evaluated_at": datetime.now().isoformat(timespec="seconds"),
        "split": "test",
        "images": len(list((DATASET_DIR / "images" / "test").glob("*.png"))),
        "instances": sum(
            len(path.read_text(encoding="utf-8").splitlines())
            for path in (DATASET_DIR / "labels" / "test").glob("*.txt")
        ),
        "device": device,
        "metrics": {
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
            "mAP50": float(metrics.box.map50),
            "mAP50_95": float(metrics.box.map),
        },
        "speed_ms_per_image": {
            key: float(value) for key, value in metrics.speed.items()
        },
        "per_class": per_class,
        "model": str(MODEL_PATH),
        "results_dir": str(metrics.save_dir),
    }
    output_json = RESULTS_DIR / "test_metrics.json"
    output_json.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    test_images = sorted((DATASET_DIR / "images" / "test").glob("*.png"))[: args.samples]
    model.predict(
        source=[str(path) for path in test_images],
        imgsz=args.imgsz,
        conf=0.25,
        device=device,
        save=True,
        project=str(RESULTS_DIR),
        name="predictions",
        exist_ok=True,
        verbose=False,
    )
    make_prediction_grid(RESULTS_DIR / "predictions", RESULTS_DIR / "prediction_grid.jpg", args.samples)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
