from __future__ import annotations

import argparse
import colorsys
import json
import math
import random
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


CLASS_NAMES = ["dado", "peao", "ficha"]
DEFAULT_SEED = 42


def get_project_root() -> Path:
    """Resolve a raiz do projeto no Terminal ou no editor de texto do Blender."""
    if bpy.data.filepath:
        current_blend = Path(bpy.data.filepath).resolve()
        if current_blend.suffix.lower() == ".blend":
            return current_blend.parent.parent
    return Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    project_root = get_project_root()
    parser = argparse.ArgumentParser(description="Generate BoardVision synthetic data")
    parser.add_argument("--output", type=Path, default=project_root / "dataset")
    parser.add_argument("--train", type=int, default=168)
    parser.add_argument("--val", type=int, default=36)
    parser.add_argument("--test", type=int, default=36)
    parser.add_argument("--resolution", type=int, default=416)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--preview", action="store_true", help="Generate only 3 images per split")
    return parser.parse_args(argv)


def clean_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def make_material(name: str, rgba: tuple[float, float, float, float], metallic=0.0, roughness=0.45):
    material = bpy.data.materials.new(name=name)
    material.use_nodes = True
    material.diffuse_color = rgba
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = rgba
    principled.inputs["Metallic"].default_value = metallic
    principled.inputs["Roughness"].default_value = roughness
    return material


def set_material_color(material, rgba, roughness=None, metallic=None) -> None:
    material.diffuse_color = rgba
    principled = material.node_tree.nodes.get("Principled BSDF")
    principled.inputs["Base Color"].default_value = rgba
    if roughness is not None:
        principled.inputs["Roughness"].default_value = roughness
    if metallic is not None:
        principled.inputs["Metallic"].default_value = metallic


def smooth_object(obj) -> None:
    if obj.type == "MESH":
        for polygon in obj.data.polygons:
            polygon.use_smooth = True


def parent_part(obj, root, role="primary"):
    obj.parent = root
    obj["material_role"] = role
    return obj


def add_bevel(obj, width=0.08, segments=3) -> None:
    modifier = obj.modifiers.new(name="Soft edges", type="BEVEL")
    modifier.width = width
    modifier.segments = segments


def create_die(primary_material, dark_material):
    root = bpy.data.objects.new("Dado", None)
    root["class_id"] = 0
    bpy.context.collection.objects.link(root)

    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0.68), scale=(0.66, 0.66, 0.66))
    body = bpy.context.object
    body.name = "Dado_Corpo"
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    add_bevel(body, width=0.12, segments=4)
    body.data.materials.append(primary_material)
    parent_part(body, root, "primary")

    pip_positions = [(-0.28, -0.28), (0.28, 0.28), (-0.28, 0.28), (0.28, -0.28), (0.0, 0.0)]
    for index, (x_pos, y_pos) in enumerate(pip_positions):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.085, location=(x_pos, y_pos, 1.355))
        pip = bpy.context.object
        pip.name = f"Dado_Ponto_{index + 1}"
        pip.scale.z = 0.35
        pip.data.materials.append(dark_material)
        smooth_object(pip)
        parent_part(pip, root, "fixed")
    return root


def create_pawn(primary_material, accent_material):
    root = bpy.data.objects.new("Peao", None)
    root["class_id"] = 1
    bpy.context.collection.objects.link(root)

    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.62, depth=0.22, location=(0, 0, 0.12))
    base = bpy.context.object
    base.name = "Peao_Base"
    add_bevel(base, width=0.07, segments=3)
    base.data.materials.append(accent_material)
    smooth_object(base)
    parent_part(base, root, "accent")

    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=0.48, radius2=0.20, depth=0.72, location=(0, 0, 0.58))
    body = bpy.context.object
    body.name = "Peao_Corpo"
    body.data.materials.append(primary_material)
    smooth_object(body)
    parent_part(body, root, "primary")

    bpy.ops.mesh.primitive_cylinder_add(vertices=40, radius=0.20, depth=0.22, location=(0, 0, 1.02))
    neck = bpy.context.object
    neck.name = "Peao_Pescoco"
    neck.data.materials.append(primary_material)
    smooth_object(neck)
    parent_part(neck, root, "primary")

    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.30, location=(0, 0, 1.32))
    head = bpy.context.object
    head.name = "Peao_Cabeca"
    head.data.materials.append(primary_material)
    smooth_object(head)
    parent_part(head, root, "primary")
    return root


def create_token(primary_material, accent_material):
    root = bpy.data.objects.new("Ficha", None)
    root["class_id"] = 2
    bpy.context.collection.objects.link(root)

    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.68, depth=0.22, location=(0, 0, 0.13))
    body = bpy.context.object
    body.name = "Ficha_Corpo"
    add_bevel(body, width=0.08, segments=3)
    body.data.materials.append(primary_material)
    smooth_object(body)
    parent_part(body, root, "primary")

    bpy.ops.mesh.primitive_torus_add(major_radius=0.43, minor_radius=0.065, major_segments=48, minor_segments=12, location=(0, 0, 0.275))
    ring = bpy.context.object
    ring.name = "Ficha_Anel"
    ring.data.materials.append(accent_material)
    smooth_object(ring)
    parent_part(ring, root, "accent")
    return root


def look_at(obj, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene(resolution: int):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.compression = 55
    scene.render.film_transparent = False
    scene.render.use_file_extension = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "Medium High Contrast"

    floor_material = make_material("Material_Fundo", (0.25, 0.30, 0.35, 1), roughness=0.72)
    die_material = make_material("Material_Dado", (0.84, 0.19, 0.15, 1), roughness=0.38)
    pip_material = make_material("Material_Pontos", (0.025, 0.025, 0.025, 1), roughness=0.55)
    pawn_material = make_material("Material_Peao", (0.10, 0.39, 0.82, 1), roughness=0.34)
    pawn_accent = make_material("Material_Peao_Detalhe", (0.05, 0.18, 0.48, 1), roughness=0.30)
    token_material = make_material("Material_Ficha", (0.10, 0.72, 0.38, 1), roughness=0.40)
    token_accent = make_material("Material_Ficha_Detalhe", (0.03, 0.30, 0.16, 1), roughness=0.30)

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "Mesa"
    floor.data.materials.append(floor_material)

    roots = [
        create_die(die_material, pip_material),
        create_pawn(pawn_material, pawn_accent),
        create_token(token_material, token_accent),
    ]

    bpy.ops.object.camera_add(location=(6.7, -6.7, 8.2))
    camera = bpy.context.object
    camera.name = "Camera_BoardVision"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 8.6
    camera.data.lens = 48
    look_at(camera, Vector((0, 0, 0.45)))
    scene.camera = camera

    bpy.ops.object.light_add(type="AREA", location=(3.5, -4.0, 7.0))
    key_light = bpy.context.object
    key_light.name = "Luz_Principal"
    key_light.data.energy = 780
    key_light.data.shape = "DISK"
    key_light.data.size = 4.5
    look_at(key_light, Vector((0, 0, 0)))

    bpy.ops.object.light_add(type="AREA", location=(-4.0, 2.5, 5.0))
    fill_light = bpy.context.object
    fill_light.name = "Luz_Preenchimento"
    fill_light.data.energy = 430
    fill_light.data.size = 5.0
    look_at(fill_light, Vector((0, 0, 0.4)))

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 6))
    sun = bpy.context.object
    sun.name = "Luz_Solar"
    sun.data.energy = 1.3
    sun.rotation_euler = (math.radians(25), math.radians(-20), math.radians(25))

    return scene, roots, floor_material, camera, key_light, fill_light, sun


def random_color(rng: random.Random, saturation=(0.55, 0.9), value=(0.55, 0.95)):
    hue = rng.random()
    sat = rng.uniform(*saturation)
    val = rng.uniform(*value)
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return (r, g, b, 1.0)


def iter_mesh_parts(root):
    stack = [root]
    while stack:
        current = stack.pop()
        if current.type == "MESH":
            yield current
        stack.extend(list(current.children))


def recolor_root(root, rng: random.Random) -> None:
    primary = random_color(rng)
    h, s, v = colorsys.rgb_to_hsv(*primary[:3])
    accent_rgb = colorsys.hsv_to_rgb(h, min(1.0, s * 1.05), max(0.20, v * 0.54))
    accent = (*accent_rgb, 1.0)
    for part in iter_mesh_parts(root):
        role = part.get("material_role", "primary")
        if role == "fixed" or not part.data.materials:
            continue
        material = part.data.materials[0]
        rgba = accent if role == "accent" else primary
        set_material_color(material, rgba, roughness=rng.uniform(0.28, 0.62))


def sample_positions(rng: random.Random, count: int, min_distance=1.85):
    positions = []
    for _ in range(count):
        for _attempt in range(200):
            candidate = Vector((rng.uniform(-2.15, 2.15), rng.uniform(-2.0, 2.0), 0))
            if all((candidate - existing).length >= min_distance for existing in positions):
                positions.append(candidate)
                break
        else:
            positions.append(Vector(((-1.8 + len(positions) * 1.8), 0, 0)))
    rng.shuffle(positions)
    return positions


def place_root_on_floor(root, clearance=0.025) -> None:
    """Move o objeto no eixo Z até seu ponto mais baixo encostar no plano."""
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    lowest_z = None
    for part in iter_mesh_parts(root):
        evaluated = part.evaluated_get(depsgraph)
        for corner in evaluated.bound_box:
            world_z = float((evaluated.matrix_world @ Vector(corner)).z)
            lowest_z = world_z if lowest_z is None else min(lowest_z, world_z)
    if lowest_z is not None:
        root.location.z += clearance - lowest_z
        bpy.context.view_layer.update()


def randomize_scene(scene, roots, floor_material, camera, key_light, fill_light, sun, rng):
    positions = sample_positions(rng, len(roots))
    object_metadata = []
    for root, position in zip(roots, positions):
        root.location = position
        root.rotation_euler = tuple(rng.uniform(-math.pi, math.pi) for _ in range(3))
        scale = rng.uniform(0.78, 1.16)
        root.scale = (scale, scale, scale)
        place_root_on_floor(root)
        recolor_root(root, rng)
        object_metadata.append({
            "class_id": int(root["class_id"]),
            "class_name": CLASS_NAMES[int(root["class_id"])],
            "location": [round(float(v), 4) for v in root.location],
            "rotation_xyz": [round(float(v), 4) for v in root.rotation_euler],
            "scale": round(scale, 4),
        })

    floor_color = random_color(rng, saturation=(0.08, 0.45), value=(0.22, 0.82))
    set_material_color(floor_material, floor_color, roughness=rng.uniform(0.58, 0.92))
    world_color = tuple(min(0.24, c * 0.25) for c in floor_color[:3]) + (1.0,)
    scene.world.color = world_color[:3]

    angle = math.radians(rng.uniform(-51, -39))
    radius = rng.uniform(8.7, 10.2)
    camera.location = (radius * math.cos(angle), radius * math.sin(angle), rng.uniform(7.3, 9.3))
    camera.data.ortho_scale = rng.uniform(7.7, 9.0)
    target = Vector((rng.uniform(-0.25, 0.25), rng.uniform(-0.25, 0.25), rng.uniform(0.35, 0.6)))
    look_at(camera, target)

    key_light.location = (rng.uniform(2.0, 5.2), rng.uniform(-5.0, -2.0), rng.uniform(5.5, 8.2))
    key_light.data.energy = rng.uniform(550, 1050)
    key_light.data.color = random_color(rng, saturation=(0.02, 0.16), value=(0.85, 1.0))[:3]
    look_at(key_light, Vector((0, 0, 0.3)))

    fill_light.location = (rng.uniform(-5.0, -2.2), rng.uniform(1.5, 4.8), rng.uniform(4.2, 7.0))
    fill_light.data.energy = rng.uniform(220, 620)
    fill_light.data.color = random_color(rng, saturation=(0.02, 0.20), value=(0.80, 1.0))[:3]
    look_at(fill_light, Vector((0, 0, 0.45)))

    sun.data.energy = rng.uniform(0.55, 1.65)
    sun.rotation_euler = tuple(rng.uniform(-0.75, 0.75) for _ in range(3))
    bpy.context.view_layer.update()
    return object_metadata, floor_color, target


def root_yolo_bbox(scene, camera, root):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    projected = []
    for part in iter_mesh_parts(root):
        evaluated = part.evaluated_get(depsgraph)
        for corner in evaluated.bound_box:
            world_corner = evaluated.matrix_world @ Vector(corner)
            coord = world_to_camera_view(scene, camera, world_corner)
            if coord.z > 0:
                projected.append((float(coord.x), float(coord.y)))
    if not projected:
        return None

    x_min = max(0.0, min(point[0] for point in projected))
    x_max = min(1.0, max(point[0] for point in projected))
    y_min = max(0.0, min(point[1] for point in projected))
    y_max = min(1.0, max(point[1] for point in projected))
    width = x_max - x_min
    height = y_max - y_min
    if width <= 0.02 or height <= 0.02 or x_min >= 1 or y_min >= 1 or x_max <= 0 or y_max <= 0:
        return None
    center_x = (x_min + x_max) / 2.0
    center_y = 1.0 - ((y_min + y_max) / 2.0)
    return center_x, center_y, width, height


def ensure_dataset_structure(dataset_root: Path, split_counts: dict[str, int]) -> None:
    dataset_root.mkdir(parents=True, exist_ok=True)
    for split in split_counts:
        (dataset_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (dataset_root / "labels" / split).mkdir(parents=True, exist_ok=True)
    (dataset_root / "classes.txt").write_text("\n".join(CLASS_NAMES) + "\n", encoding="utf-8")
    yaml_text = (
        "path: .\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "names:\n"
        "  0: dado\n"
        "  1: peao\n"
        "  2: ficha\n"
    )
    (dataset_root / "data.yaml").write_text(yaml_text, encoding="utf-8")


def generate_dataset(args, scene, roots, floor_material, camera, key_light, fill_light, sun):
    dataset_root = args.output.resolve()
    split_counts = {"train": args.train, "val": args.val, "test": args.test}
    if args.preview:
        split_counts = {name: min(3, count) for name, count in split_counts.items()}
    ensure_dataset_structure(dataset_root, split_counts)

    metadata_path = dataset_root / "metadata.jsonl"
    total = sum(split_counts.values())
    completed = 0
    records = []

    for split_index, (split, count) in enumerate(split_counts.items()):
        split_rng = random.Random(args.seed + split_index * 10_000)
        for image_index in range(count):
            filename = f"{split}_{image_index:04d}"
            for attempt in range(25):
                object_metadata, floor_color, target = randomize_scene(
                    scene, roots, floor_material, camera, key_light, fill_light, sun, split_rng
                )
                boxes = [root_yolo_bbox(scene, camera, root) for root in roots]
                if all(box is not None for box in boxes):
                    break
            else:
                raise RuntimeError(f"Could not create valid boxes for {filename}")

            image_path = dataset_root / "images" / split / f"{filename}.png"
            label_path = dataset_root / "labels" / split / f"{filename}.txt"
            scene.render.filepath = str(image_path)
            bpy.ops.render.render(write_still=True)

            label_lines = []
            for root, box, item in zip(roots, boxes, object_metadata):
                class_id = int(root["class_id"])
                center_x, center_y, width, height = box
                label_lines.append(
                    f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}"
                )
                item["bbox_yolo"] = [round(center_x, 6), round(center_y, 6), round(width, 6), round(height, 6)]
            label_path.write_text("\n".join(label_lines) + "\n", encoding="utf-8")

            records.append({
                "split": split,
                "image": image_path.name,
                "resolution": [args.resolution, args.resolution],
                "objects": object_metadata,
                "camera": {
                    "location": [round(float(value), 4) for value in camera.location],
                    "ortho_scale": round(float(camera.data.ortho_scale), 4),
                    "target": [round(float(value), 4) for value in target],
                },
                "lighting": {
                    "key_energy": round(float(key_light.data.energy), 3),
                    "fill_energy": round(float(fill_light.data.energy), 3),
                    "sun_energy": round(float(sun.data.energy), 3),
                },
                "floor_color": [round(float(value), 4) for value in floor_color],
            })
            completed += 1
            print(f"[BoardVision] {completed:04d}/{total:04d} | {split}/{filename}.png")

    with metadata_path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = {
        "project": "BoardVision",
        "task": "object_detection",
        "classes": CLASS_NAMES,
        "resolution": args.resolution,
        "seed": args.seed,
        "splits": split_counts,
        "images": total,
        "instances": total * len(CLASS_NAMES),
    }
    (dataset_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    args = parse_args()
    project_root = get_project_root()
    clean_scene()
    scene, roots, floor_material, camera, key_light, fill_light, sun = setup_scene(args.resolution)

    scene_rng = random.Random(args.seed)
    randomize_scene(scene, roots, floor_material, camera, key_light, fill_light, sun, scene_rng)
    blend_path = project_root / "blender" / "ProjetoFinal.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    summary = generate_dataset(args, scene, roots, floor_material, camera, key_light, fill_light, sun)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    print("[BoardVision] Generation complete")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
