"""Validate YOLO labels and create a visual annotation preview."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CLASS_NAMES = ["dado", "peao", "ficha"]
CLASS_COLORS = [(239, 78, 78), (77, 166, 255), (56, 190, 116)]


def parse_args():
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=project_root / "dataset")
    parser.add_argument("--output", type=Path, default=project_root / "results")
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def parse_label(path: Path):
    labels = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split()
        if len(fields) != 5:
            raise ValueError(f"{path}:{line_number}: expected 5 fields, found {len(fields)}")
        class_id = int(fields[0])
        values = [float(value) for value in fields[1:]]
        if class_id not in range(len(CLASS_NAMES)):
            raise ValueError(f"{path}:{line_number}: invalid class {class_id}")
        if not all(0.0 <= value <= 1.0 for value in values):
            raise ValueError(f"{path}:{line_number}: coordinate outside [0, 1]")
        if values[2] <= 0 or values[3] <= 0:
            raise ValueError(f"{path}:{line_number}: non-positive box")
        labels.append((class_id, *values))
    return labels


def draw_boxes(image_path: Path, labels):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=15)
    width, height = image.size
    for class_id, center_x, center_y, box_width, box_height in labels:
        x1 = int((center_x - box_width / 2) * width)
        y1 = int((center_y - box_height / 2) * height)
        x2 = int((center_x + box_width / 2) * width)
        y2 = int((center_y + box_height / 2) * height)
        color = CLASS_COLORS[class_id]
        draw.rectangle((x1, y1, x2, y2), outline=color, width=4)
        label = CLASS_NAMES[class_id]
        left, top, right, bottom = draw.textbbox((x1, y1), label, font=font)
        draw.rectangle((x1, y1 - (bottom - top) - 7, x1 + (right - left) + 8, y1), fill=color)
        draw.text((x1 + 4, y1 - (bottom - top) - 4), label, fill="white", font=font)
    return image


def make_preview(records, output_path: Path, sample_count: int, seed: int):
    rng = random.Random(seed)
    chosen = rng.sample(records, min(sample_count, len(records)))
    tiles = [draw_boxes(image_path, labels).resize((320, 320)) for image_path, labels in chosen]
    columns = 4
    rows = (len(tiles) + columns - 1) // columns
    canvas = Image.new("RGB", (columns * 320, rows * 320), "white")
    for index, tile in enumerate(tiles):
        canvas.paste(tile, ((index % columns) * 320, (index // columns) * 320))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, quality=95)


def main():
    args = parse_args()
    dataset = args.dataset.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    errors = []
    split_summary = {}
    class_counts = Counter()
    all_records = []
    seen_names = set()

    for split in ("train", "val", "test"):
        image_dir = dataset / "images" / split
        label_dir = dataset / "labels" / split
        images = sorted(image_dir.glob("*.png"))
        labels = sorted(label_dir.glob("*.txt"))
        image_stems = {path.stem for path in images}
        label_stems = {path.stem for path in labels}
        missing_labels = sorted(image_stems - label_stems)
        missing_images = sorted(label_stems - image_stems)
        if missing_labels:
            errors.append(f"{split}: images without labels: {missing_labels[:5]}")
        if missing_images:
            errors.append(f"{split}: labels without images: {missing_images[:5]}")
        duplicates = seen_names.intersection(image_stems)
        if duplicates:
            errors.append(f"{split}: duplicate stems across splits: {sorted(duplicates)[:5]}")
        seen_names.update(image_stems)

        split_instances = 0
        split_class_counts = Counter()
        dimensions = Counter()
        for image_path in images:
            try:
                with Image.open(image_path) as image:
                    dimensions[image.size] += 1
                label_path = label_dir / f"{image_path.stem}.txt"
                parsed = parse_label(label_path)
                if not parsed:
                    errors.append(f"{label_path}: empty label")
                    continue
                split_instances += len(parsed)
                split_class_counts.update(label[0] for label in parsed)
                class_counts.update(label[0] for label in parsed)
                all_records.append((image_path, parsed))
            except Exception as exc:
                errors.append(str(exc))

        split_summary[split] = {
            "images": len(images),
            "labels": len(labels),
            "instances": split_instances,
            "classes": {CLASS_NAMES[key]: split_class_counts[key] for key in range(len(CLASS_NAMES))},
            "dimensions": {f"{w}x{h}": count for (w, h), count in dimensions.items()},
        }

    preview_path = args.output / "annotation_preview.png"
    if all_records:
        make_preview(all_records, preview_path, args.samples, args.seed)

    report = {
        "valid": not errors,
        "dataset": str(dataset),
        "splits": split_summary,
        "total_images": sum(item["images"] for item in split_summary.values()),
        "total_instances": sum(item["instances"] for item in split_summary.values()),
        "class_distribution": {CLASS_NAMES[key]: class_counts[key] for key in range(len(CLASS_NAMES))},
        "errors": errors,
        "preview": str(preview_path),
    }
    report_path = args.output / "dataset_validation.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
