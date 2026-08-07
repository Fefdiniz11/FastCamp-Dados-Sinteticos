from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path

import torch
import yaml
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "dataset"
RESULTS_DIR = ROOT / "results"
MODELS_DIR = ROOT / "models"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--imgsz", type=int, default=416)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--patience", type=int, default=8)
    parser.add_argument("--checkpoint", default="yolov8n.pt")
    parser.add_argument("--device", default="auto", help="auto, mps, cpu ou índice CUDA")
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
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "path": str(DATASET_DIR),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": {0: "dado", 1: "peao", 2: "ficha"},
    }
    output = RESULTS_DIR / "data_local.yaml"
    output.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return output


def main() -> None:
    args = parse_args()
    device = select_device(args.device)
    data_yaml = write_runtime_yaml()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[BoardVision] dispositivo: {device}")
    print(f"[BoardVision] dataset: {DATASET_DIR}")

    model = YOLO(args.checkpoint)
    train_result = model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device=device,
        workers=0,
        optimizer="AdamW",
        lr0=0.001,
        seed=42,
        deterministic=True,
        pretrained=True,
        plots=True,
        val=True,
        cache=False,
        project=str(RESULTS_DIR),
        name="boardvision_train",
        exist_ok=True,
        verbose=True,
    )

    run_dir = Path(train_result.save_dir)
    best_source = run_dir / "weights" / "best.pt"
    best_target = MODELS_DIR / "best.pt"
    if not best_source.exists():
        raise FileNotFoundError(f"Modelo treinado não encontrado: {best_source}")
    shutil.copy2(best_source, best_target)

    metadata = {
        "project": "BoardVision",
        "trained_at": datetime.now().isoformat(timespec="seconds"),
        "architecture": "YOLOv8n",
        "checkpoint": args.checkpoint,
        "epochs_requested": args.epochs,
        "image_size": args.imgsz,
        "batch": args.batch,
        "patience": args.patience,
        "optimizer": "AdamW",
        "initial_learning_rate": 0.001,
        "seed": 42,
        "device": device,
        "run_dir": str(run_dir),
        "best_model": str(best_target),
    }
    (RESULTS_DIR / "training_config.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[BoardVision] melhor modelo: {best_target}")


if __name__ == "__main__":
    main()
