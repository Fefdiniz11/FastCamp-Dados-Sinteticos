"""Gera slides, narração e o vídeo de pitch do BoardVision."""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PITCH_DIR = ROOT / "pitch"
BUILD_DIR = PITCH_DIR / ".pitch_build"
VIDEO_PATH = PITCH_DIR / "BoardVision-Pitch-FernandaDiniz.mp4"
WIDTH, HEIGHT = 1920, 1080

NAVY = "#16324F"
TEAL = "#00A6A6"
SKY = "#DFF7F7"
CORAL = "#FF6B6B"
LIGHT = "#F4F7FA"
TEXT = "#263442"
MUTED = "#647789"

FONT_DIR = Path("/System/Library/Fonts/Supplemental")
FONT_REGULAR = FONT_DIR / "Arial.ttf"
FONT_BOLD = FONT_DIR / "Arial Bold.ttf"

SLIDES = [
    {
        "eyebrow": "PROJETO FINAL — DADOS SINTÉTICOS",
        "title": "BoardVision",
        "subtitle": "Do Blender a um detector de peças de jogos",
        "bullets": ["Dado", "Peão", "Ficha"],
        "image": ROOT / "dataset" / "images" / "test" / "test_0000.png",
        "narration": (
            "Olá, eu sou Fernanda Diniz e este é o BoardVision, meu projeto final do curso de Dados Sintéticos. "
            "O objetivo foi construir um pipeline completo de visão computacional, começando no Blender e "
            "terminando em um modelo capaz de detectar três peças de jogos: dado, peão e ficha."
        ),
    },
    {
        "eyebrow": "O PROBLEMA",
        "title": "Coleta e anotação custam tempo",
        "subtitle": "Dados sintéticos transformam a cena 3D em uma fonte controlada de exemplos.",
        "bullets": ["Menos anotação manual", "Diversidade controlada", "Pipeline reproduzível"],
        "image": ROOT / "results" / "annotation_preview.png",
        "narration": (
            "Treinar detectores normalmente exige muitas fotografias e anotações manuais. Isso demanda tempo e "
            "pode produzir um conjunto pouco variado. A proposta do BoardVision foi substituir essa etapa por uma "
            "cena sintética controlada, na qual a posição e os limites dos objetos já são conhecidos pelo simulador."
        ),
    },
    {
        "eyebrow": "A SOLUÇÃO",
        "title": "Imagem e rótulo no mesmo processo",
        "subtitle": "Modelagem procedural + randomização + projeção geométrica",
        "bullets": ["Objetos criados por script", "Pose, cor, câmera e luz aleatórias", "Bounding boxes no formato YOLO"],
        "image": ROOT / "results" / "annotation_preview.png",
        "narration": (
            "Os três objetos foram construídos proceduralmente no Blender, sem depender de modelos externos. Um "
            "script em Python com a API bi pi i randomiza posição, rotação, escala, cor, material, fundo, câmera e "
            "iluminação. Para cada cena, o mesmo script renderiza a imagem e projeta a geometria tridimensional na "
            "câmera, gerando automaticamente as caixas no formato YOLO."
        ),
    },
    {
        "eyebrow": "O DATASET",
        "title": "240 imagens • 720 anotações",
        "subtitle": "Três classes balanceadas em 416 × 416 pixels",
        "bullets": ["168 treino — 70%", "36 validação — 15%", "36 teste — 15%", "Zero erros na validação"],
        "image": ROOT / "dataset" / "images" / "test" / "test_0012.png",
        "narration": (
            "O dataset final possui duzentas e quarenta imagens com resolução de quatrocentos e dezesseis por "
            "quatrocentos e dezesseis pixels e setecentos e vinte objetos anotados. Foram usadas cento e sessenta e "
            "oito imagens para treino, trinta e seis para validação e trinta e seis para teste. As três classes "
            "ficaram balanceadas. Um validador automático conferiu todos os pares e não encontrou erros."
        ),
    },
    {
        "eyebrow": "TREINAMENTO",
        "title": "YOLOv8n em 20 épocas",
        "subtitle": "Transferência de aprendizado e aceleração Apple MPS",
        "bullets": ["Precisão 97,7%", "Recall 100%", "mAP@50 99,5%", "mAP@50–95 80,9%"],
        "image": ROOT / "results" / "boardvision_train" / "results.png",
        "narration": (
            "O detector escolhido foi o YOLO versão oito nano, treinado por vinte épocas com transferência de "
            "aprendizado. No conjunto de teste separado, o modelo alcançou precisão de noventa e sete vírgula sete "
            "por cento, recall de cem por cento, mAP cinquenta de noventa e nove vírgula cinco por cento e mAP de "
            "cinquenta a noventa e cinco de oitenta vírgula nove por cento."
        ),
    },
    {
        "eyebrow": "RESULTADO FINAL",
        "title": "Um pipeline completo e reproduzível",
        "subtitle": "Cena, código, dataset, modelo, métricas e documentação",
        "bullets": ["Boa detecção sob variações visuais", "Próximo passo: reduzir o domain gap", "Projeto pronto para novos ciclos"],
        "image": ROOT / "results" / "prediction_grid.jpg",
        "narration": (
            "As predições mostram boa identificação mesmo com mudanças de cor, luz, posição e escala. Os principais "
            "diferenciais são a reprodução completa por scripts, as anotações sem trabalho manual e a entrega de "
            "todos os artefatos. A principal limitação é o domain gap, porque o teste ainda é sintético. Como próximo "
            "passo, eu incluiria texturas e fundos reais e avaliaria o modelo em fotografias. O projeto demonstra, de "
            "ponta a ponta, como dados sintéticos podem acelerar uma solução de visão computacional. Obrigada."
        ),
    },
]


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size=size)


def wrapped_lines(text: str, max_chars: int) -> list[str]:
    return textwrap.wrap(text, width=max_chars, break_long_words=False)


def paste_contain(canvas: Image.Image, source_path: Path, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    source = Image.open(source_path).convert("RGB")
    source.thumbnail((x1 - x0, y1 - y0), Image.Resampling.LANCZOS)
    x = x0 + (x1 - x0 - source.width) // 2
    y = y0 + (y1 - y0 - source.height) // 2
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle((x + 16, y + 18, x + source.width + 16, y + source.height + 18), radius=28, fill=(20, 45, 65, 55))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow)
    mask = Image.new("L", source.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, source.width, source.height), radius=24, fill=255)
    canvas.paste(source, (x, y), mask)


def render_slide(index: int, slide: dict, output: Path) -> None:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), LIGHT)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((0, 0, WIDTH, 22), fill=TEAL)
    draw.ellipse((-260, 760, 360, 1380), fill=SKY)
    draw.ellipse((1540, -320, 2200, 340), fill="#E8E5FF")

    draw.text((96, 80), slide["eyebrow"], font=font(FONT_BOLD, 27), fill=TEAL)
    title_y = 145
    for line in wrapped_lines(slide["title"], 27):
        draw.text((96, title_y), line, font=font(FONT_BOLD, 64), fill=NAVY)
        title_y += 76
    title_y += 14
    for line in wrapped_lines(slide["subtitle"], 49):
        draw.text((96, title_y), line, font=font(FONT_REGULAR, 30), fill=MUTED)
        title_y += 42

    bullet_y = max(445, title_y + 28)
    for bullet in slide["bullets"]:
        draw.rounded_rectangle((96, bullet_y + 8, 118, bullet_y + 30), radius=6, fill=CORAL)
        for line_index, line in enumerate(wrapped_lines(bullet, 40)):
            draw.text((142, bullet_y + line_index * 37), line, font=font(FONT_REGULAR, 30), fill=TEXT)
        bullet_y += 68

    image_box = (1015, 115, 1825, 905)
    draw.rounded_rectangle(image_box, radius=32, fill="white", outline="#CBD7E1", width=3)
    paste_contain(canvas, slide["image"], (1045, 145, 1795, 875))

    draw.line((96, 984, 1824, 984), fill="#CAD5DF", width=2)
    draw.text((96, 1004), "BoardVision", font=font(FONT_BOLD, 24), fill=NAVY)
    footer = f"Fernanda Faria Diniz  •  Projeto Final  •  {index + 1}/{len(SLIDES)}"
    footer_width = draw.textbbox((0, 0), footer, font=font(FONT_REGULAR, 22))[2]
    draw.text((1824 - footer_width, 1006), footer, font=font(FONT_REGULAR, 22), fill=MUTED)
    canvas.convert("RGB").save(output, quality=95)


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def build_video() -> None:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    segment_paths = []
    for index, slide in enumerate(SLIDES, start=1):
        image_path = BUILD_DIR / f"slide_{index:02d}.png"
        audio_path = BUILD_DIR / f"slide_{index:02d}.aiff"
        segment_path = BUILD_DIR / f"segment_{index:02d}.mp4"
        render_slide(index - 1, slide, image_path)
        run(["say", "-v", "Luciana", "-r", "172", "-o", str(audio_path), slide["narration"]])
        run([
            "ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(image_path),
            "-i", str(audio_path), "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", "-r", "30", "-shortest", str(segment_path),
        ])
        segment_paths.append(segment_path)

    concat_file = BUILD_DIR / "segments.txt"
    concat_file.write_text("".join(f"file '{path}'\n" for path in segment_paths), encoding="utf-8")
    run([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c", "copy", "-movflags", "+faststart", str(VIDEO_PATH),
    ])
    print(VIDEO_PATH)


if __name__ == "__main__":
    build_video()
