"""Executa o modelo BoardVision em uma imagem, vídeo ou pasta."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "models" / "best.pt"
RESULTS_DIR = ROOT / "results"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Caminho de uma imagem, vídeo ou pasta")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=416)
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


def main() -> None:
    args = parse_args()
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {MODEL_PATH}")
    source = Path(args.source).expanduser().resolve()
    if not source.exists():
        raise FileNotFoundError(f"Entrada não encontrada: {source}")

    model = YOLO(str(MODEL_PATH))
    model.predict(
        source=str(source),
        imgsz=args.imgsz,
        conf=args.conf,
        device=select_device(args.device),
        save=True,
        project=str(RESULTS_DIR),
        name="inference",
        exist_ok=True,
    )
    print(f"Resultado salvo em: {RESULTS_DIR / 'inference'}")


if __name__ == "__main__":
    main()
