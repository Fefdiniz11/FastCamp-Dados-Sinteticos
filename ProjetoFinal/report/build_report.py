"""Gera o relatório técnico final do projeto BoardVision em PDF."""

from __future__ import annotations

from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "report" / "Relatorio12-FernandaDiniz.pdf"
NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#00A6A6")
SKY = colors.HexColor("#DFF7F7")
CORAL = colors.HexColor("#FF6B6B")
LIGHT = colors.HexColor("#F4F7FA")
MID = colors.HexColor("#D5DEE8")
TEXT = colors.HexColor("#263442")


def register_fonts() -> None:
    font_dir = Path("/System/Library/Fonts/Supplemental")
    pdfmetrics.registerFont(TTFont("Arial", str(font_dir / "Arial.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Bold", str(font_dir / "Arial Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Arial-Italic", str(font_dir / "Arial Italic.ttf")))


def make_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            fontName="Arial-Bold",
            fontSize=23,
            leading=28,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=7 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="ReportSubtitle",
            fontName="Arial",
            fontSize=12,
            leading=17,
            textColor=TEAL,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1Custom",
            fontName="Arial-Bold",
            fontSize=14,
            leading=18,
            textColor=NAVY,
            spaceBefore=3 * mm,
            spaceAfter=2.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Custom",
            fontName="Arial-Bold",
            fontSize=11.5,
            leading=15,
            textColor=TEAL,
            spaceBefore=2.5 * mm,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            fontName="Arial",
            fontSize=10.2,
            leading=14.5,
            textColor=TEXT,
            alignment=TA_JUSTIFY,
            spaceAfter=2.4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodySmall",
            fontName="Arial",
            fontSize=8.8,
            leading=12,
            textColor=TEXT,
            alignment=TA_LEFT,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            fontName="Arial-Italic",
            fontSize=8.2,
            leading=11,
            textColor=colors.HexColor("#556574"),
            alignment=TA_CENTER,
            spaceBefore=1.3 * mm,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetricValue",
            fontName="Arial-Bold",
            fontSize=17,
            leading=20,
            textColor=NAVY,
            alignment=TA_CENTER,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MetricLabel",
            fontName="Arial",
            fontSize=8.2,
            leading=10,
            textColor=colors.HexColor("#516171"),
            alignment=TA_CENTER,
        )
    )
    return styles


def fitted_image(path: Path, max_width: float, max_height: float) -> Image:
    with PILImage.open(path) as source:
        width, height = source.size
    ratio = min(max_width / width, max_height / height)
    return Image(str(path), width=width * ratio, height=height * ratio)


def figure(path: Path, caption_text: str, styles, max_width=168 * mm, max_height=102 * mm):
    return KeepTogether(
        [
            fitted_image(path, max_width, max_height),
            Paragraph(caption_text, styles["Caption"]),
        ]
    )


def section(title: str, styles):
    return Paragraph(title, styles["H1Custom"])


def subsection(title: str, styles):
    return Paragraph(title, styles["H2Custom"])


def body(text: str, styles):
    return Paragraph(text, styles["BodyCustom"])


def styled_table(data, widths, header=True, font_size=9):
    table = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="CENTER")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Arial"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 3),
        ("TEXTCOLOR", (0, 0), (-1, -1), TEXT),
        ("GRID", (0, 0), (-1, -1), 0.4, MID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, LIGHT]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        commands.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
            ]
        )
    table.setStyle(TableStyle(commands))
    return table


def footer(canvas, doc):
    canvas.saveState()
    width, _ = A4
    canvas.setStrokeColor(MID)
    canvas.setLineWidth(0.4)
    canvas.line(20 * mm, 14 * mm, width - 20 * mm, 14 * mm)
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#607080"))
    canvas.drawString(20 * mm, 9 * mm, "BoardVision — Relatório 12")
    canvas.drawRightString(width - 20 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def build_report() -> None:
    register_fonts()
    styles = make_styles()
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=20 * mm,
        title="Relatório 12 – Projeto Final: BoardVision",
        author="Fernanda Faria Diniz",
        subject="Geração de dados sintéticos e detecção de objetos",
    )

    story = []
    story.append(Spacer(1, 9 * mm))
    story.append(Paragraph("RELATÓRIO 12 — PROJETO FINAL", styles["ReportSubtitle"]))
    story.append(Paragraph("BoardVision", styles["ReportTitle"]))
    story.append(
        Paragraph(
            "Geração de dataset sintético no Blender e treinamento de um detector de peças de jogos",
            styles["ReportSubtitle"],
        )
    )
    story.append(Paragraph("Fernanda Faria Diniz", ParagraphStyle(
        "Author", parent=styles["BodyCustom"], fontName="Arial-Bold", fontSize=12,
        alignment=TA_CENTER, textColor=NAVY, spaceAfter=1.5 * mm
    )))
    story.append(Paragraph("FastCamp — Dados Sintéticos | Agosto de 2026", ParagraphStyle(
        "Course", parent=styles["BodySmall"], alignment=TA_CENTER, textColor=colors.HexColor("#607080")
    )))
    story.append(Spacer(1, 6 * mm))
    cover_image = fitted_image(ROOT / "dataset" / "images" / "test" / "test_0000.png", 100 * mm, 82 * mm)
    cover_box = Table([[cover_image]], colWidths=[106 * mm])
    cover_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    story.append(cover_box)
    story.append(Spacer(1, 5 * mm))
    metric_data = [[
        [Paragraph("240", styles["MetricValue"]), Paragraph("imagens", styles["MetricLabel"])],
        [Paragraph("720", styles["MetricValue"]), Paragraph("anotações", styles["MetricLabel"])],
        [Paragraph("99,5%", styles["MetricValue"]), Paragraph("mAP@50", styles["MetricLabel"])],
        [Paragraph("97,7%", styles["MetricValue"]), Paragraph("precisão", styles["MetricLabel"])],
    ]]
    cards = Table(metric_data, colWidths=[41 * mm] * 4)
    cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SKY),
        ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(cards)
    story.append(Spacer(1, 6 * mm))
    story.append(body(
        "Este relatório descreve o desenvolvimento de um pipeline completo para detecção de objetos, "
        "desde a criação procedural e a randomização da cena no Blender até a anotação automática, "
        "o treinamento do YOLOv8n e a avaliação em um conjunto sintético de teste.", styles
    ))

    story.append(PageBreak())
    story.append(section("1. Introdução", styles))
    story.append(body(
        "Modelos de visão computacional dependem de imagens representativas e anotações confiáveis. "
        "Em dados reais, obter variedade suficiente e desenhar manualmente caixas em cada imagem pode "
        "ser demorado. A geração sintética permite controlar a cena e usar a própria geometria 3D para "
        "criar as anotações ao mesmo tempo que as imagens são renderizadas.", styles
    ))
    story.append(body(
        "O projeto final recebeu o nome <b>BoardVision</b> e integra os conhecimentos desenvolvidos ao "
        "longo do curso: preparação de cenas no Blender, uso da API Python <i>bpy</i>, randomização de "
        "domínio, organização de datasets, anotações no formato YOLO, treinamento por transferência de "
        "aprendizado e análise de métricas.", styles
    ))
    story.append(section("2. Definição do problema e escopo", styles))
    story.append(body(
        "A tarefa escolhida foi a <b>detecção de objetos</b>. Dada uma imagem de uma superfície de jogo, "
        "o modelo deve informar onde cada peça aparece e classificá-la como <b>dado</b>, <b>peão</b> ou "
        "<b>ficha</b>. O escopo foi definido para ser simples e permitir a execução completa do pipeline "
        "em um computador pessoal, sem depender de ativos externos.", styles
    ))
    story.append(styled_table([
        ["ID", "Classe", "Construção no Blender", "Características visuais"],
        ["0", "dado", "cubo chanfrado e cinco marcações", "volume alto e face quadrada"],
        ["1", "peão", "base, corpo cônico e esfera", "silhueta vertical"],
        ["2", "ficha", "cilindro baixo e aro superior", "silhueta circular e baixa"],
    ], [13 * mm, 25 * mm, 67 * mm, 59 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(subsection("Variações planejadas", styles))
    story.append(body(
        "Cada imagem apresenta os três objetos. O script varia a posição no plano, a rotação em torno do "
        "eixo vertical, a escala, as cores e a rugosidade dos materiais. Também são modificados o fundo, "
        "a posição e o enquadramento da câmera, a energia e a cor de duas luzes de área e a direção de uma "
        "luz solar. Uma distância mínima reduz sobreposições extremas, mas ainda permite cenas com objetos próximos.", styles
    ))
    pipeline = Table([[
        Paragraph("Cena 3D", styles["BodySmall"]),
        Paragraph("→", styles["MetricValue"]),
        Paragraph("Randomização", styles["BodySmall"]),
        Paragraph("→", styles["MetricValue"]),
        Paragraph("Imagem + rótulo", styles["BodySmall"]),
        Paragraph("→", styles["MetricValue"]),
        Paragraph("YOLOv8n", styles["BodySmall"]),
    ]], colWidths=[28 * mm, 8 * mm, 32 * mm, 8 * mm, 38 * mm, 8 * mm, 28 * mm])
    pipeline.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), SKY),
        ("BACKGROUND", (2, 0), (2, 0), SKY),
        ("BACKGROUND", (4, 0), (4, 0), SKY),
        ("BACKGROUND", (6, 0), (6, 0), SKY),
        ("BOX", (0, 0), (0, 0), 0.7, TEAL),
        ("BOX", (2, 0), (2, 0), 0.7, TEAL),
        ("BOX", (4, 0), (4, 0), 0.7, TEAL),
        ("BOX", (6, 0), (6, 0), 0.7, TEAL),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(pipeline)

    story.append(PageBreak())
    story.append(section("3. Preparação da cena no Blender", styles))
    story.append(body(
        "Os três modelos foram construídos proceduralmente pelo próprio script. Essa escolha deixa o projeto "
        "independente de downloads e permite reconstruir a cena desde uma instalação limpa do Blender. O dado "
        "usa um cubo com bordas chanfradas e cinco pequenos cilindros escuros na face superior; o peão combina "
        "uma base cilíndrica, um corpo cônico e uma esfera; a ficha combina um disco com um aro.", styles
    ))
    story.append(body(
        "A cena contém um plano de apoio, uma câmera ortográfica inclinada, duas luzes de área e uma luz do tipo "
        "Sun. O renderizador utilizado foi o Eevee, escolhido por oferecer boa velocidade para um dataset desse "
        "porte. Sombras de contato, oclusão ambiente e materiais com diferentes níveis de rugosidade ajudam a "
        "produzir pistas visuais sem tornar a renderização pesada.", styles
    ))
    story.append(figure(
        ROOT / "dataset" / "images" / "test" / "test_0012.png",
        "Figura 1 — Exemplo de cena sintética renderizada com os três objetos. Fonte: elaboração própria (2026).",
        styles, max_height=105 * mm
    ))
    story.append(subsection("Automação e reprodutibilidade", styles))
    story.append(body(
        "O arquivo <b>blender/generate_dataset.py</b> configura toda a cena, recebe por linha de comando as "
        "quantidades de treino, validação e teste, a resolução e a semente aleatória. A semente 42 permite "
        "repetir a mesma sequência de imagens. Ao final da execução, o script também salva o arquivo "
        "<b>boardvision_scene.blend</b>, além de metadados em JSON Lines com os parâmetros usados em cada cena.", styles
    ))

    story.append(PageBreak())
    story.append(section("4. Geração e anotação automática", styles))
    story.append(subsection("Randomização da cena", styles))
    story.append(body(
        "Para cada renderização, os objetos recebem posições amostradas em uma área útil do plano, com distância "
        "mínima aproximada de 1,85 unidade. A rotação cobre 360 graus e a escala varia entre 0,78 e 1,16. A câmera "
        "ortográfica muda levemente de posição, altura, alvo e escala. As energias das luzes também são sorteadas, "
        "produzindo sombras e contrastes diferentes. Cores foram amostradas no espaço HSV para manter variedade "
        "sem gerar objetos excessivamente escuros.", styles
    ))
    story.append(subsection("Bounding boxes no formato YOLO", styles))
    story.append(body(
        "Depois de atualizar a cena, o script percorre os vértices das caixas envolventes de todos os componentes "
        "de cada objeto. Esses pontos são transformados para coordenadas de câmera com "
        "<i>world_to_camera_view</i>. Os valores mínimos e máximos formam a caixa 2D, que é recortada aos limites "
        "da imagem e convertida para centro, largura e altura normalizados.", styles
    ))
    formula = Table([[Paragraph(
        "<b>classe&nbsp;&nbsp; x<sub>centro</sub>&nbsp;&nbsp; y<sub>centro</sub>&nbsp;&nbsp; largura&nbsp;&nbsp; altura</b>",
        ParagraphStyle("Formula", parent=styles["BodyCustom"], alignment=TA_CENTER, textColor=NAVY)
    )]], colWidths=[150 * mm])
    formula.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SKY),
        ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(formula)
    story.append(Spacer(1, 4 * mm))
    story.append(figure(
        ROOT / "results" / "annotation_preview.png",
        "Figura 2 — Amostra das anotações geradas automaticamente. Vermelho: dado; azul: peão; verde: ficha. Fonte: elaboração própria (2026).",
        styles, max_height=105 * mm
    ))

    story.append(PageBreak())
    story.append(section("5. Dataset e controle de qualidade", styles))
    story.append(body(
        "Foram geradas 240 imagens PNG de 416 × 416 pixels. Como cada imagem contém um exemplar de cada classe, "
        "o conjunto possui 720 instâncias e distribuição perfeitamente equilibrada. A separação foi realizada "
        "durante a geração para manter conjuntos independentes.", styles
    ))
    story.append(styled_table([
        ["Divisão", "Imagens", "Instâncias", "Dado", "Peão", "Ficha", "Proporção"],
        ["Treino", "168", "504", "168", "168", "168", "70%"],
        ["Validação", "36", "108", "36", "36", "36", "15%"],
        ["Teste", "36", "108", "36", "36", "36", "15%"],
        ["Total", "240", "720", "240", "240", "240", "100%"],
    ], [35 * mm, 22 * mm, 25 * mm, 18 * mm, 18 * mm, 18 * mm, 22 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(subsection("Estrutura de pastas", styles))
    structure = [
        ["dataset/images/train", "168 imagens para ajuste dos pesos"],
        ["dataset/images/val", "36 imagens para acompanhar o treinamento"],
        ["dataset/images/test", "36 imagens usadas somente na avaliação final"],
        ["dataset/labels/{split}", "um arquivo TXT YOLO para cada imagem"],
        ["dataset/metadata.jsonl", "parâmetros de cena e caixas por imagem"],
        ["dataset/data.yaml", "classes e caminhos usados pelo detector"],
    ]
    story.append(styled_table([["Caminho", "Conteúdo"]] + structure, [65 * mm, 99 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(subsection("Validação automática", styles))
    story.append(body(
        "O script <b>scripts/validate_dataset.py</b> verifica correspondência entre imagens e rótulos, dimensões, "
        "identificadores de classe, quantidade de campos, largura e altura positivas e coordenadas normalizadas. "
        "O resultado foi <b>240 pares válidos, 720 instâncias e zero erros</b>. Além do arquivo JSON de auditoria, "
        "a grade da Figura 2 foi usada para inspeção visual das caixas.", styles
    ))
    validation = Table([[
        Paragraph("OK — 240 imagens", styles["MetricLabel"]),
        Paragraph("OK — 240 rótulos", styles["MetricLabel"]),
        Paragraph("OK — 720 instâncias", styles["MetricLabel"]),
        Paragraph("OK — 0 erros", styles["MetricLabel"]),
    ]], colWidths=[41 * mm] * 4)
    validation.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SKY),
        ("BOX", (0, 0), (-1, -1), 0.6, TEAL),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(validation)

    story.append(PageBreak())
    story.append(section("6. Treinamento do modelo", styles))
    story.append(body(
        "Foi escolhida a arquitetura <b>YOLOv8n</b>, uma versão compacta adequada para experimentos rápidos de "
        "detecção. O treinamento utilizou transferência de aprendizado a partir de pesos pré-treinados. A camada "
        "de saída foi adaptada para as três classes do projeto, enquanto o restante da rede foi refinado com as "
        "imagens sintéticas.", styles
    ))
    story.append(styled_table([
        ["Parâmetro", "Valor"],
        ["Arquitetura", "YOLOv8n — 3,0 milhões de parâmetros"],
        ["Épocas", "20"],
        ["Tamanho de entrada", "416 × 416"],
        ["Batch", "16"],
        ["Otimizador", "AdamW"],
        ["Taxa de aprendizado inicial", "0,001"],
        ["Semente", "42"],
        ["Dispositivo", "Apple MPS (GPU do Mac)"],
    ], [68 * mm, 96 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(figure(
        ROOT / "results" / "boardvision_train" / "results.png",
        "Figura 3 — Curvas de perda, precisão, recall e mAP ao longo das 20 épocas. Fonte: resultados do treinamento (2026).",
        styles, max_height=102 * mm
    ))
    story.append(body(
        "As perdas de caixa, classificação e distribuição diminuíram de forma consistente. O mAP@50 subiu "
        "rapidamente e permaneceu próximo de 0,995; já o mAP@50–95 continuou melhorando ao longo das épocas, "
        "mostrando refinamento gradual da posição das caixas. O melhor peso foi salvo em <b>models/best.pt</b>.", styles
    ))

    story.append(PageBreak())
    story.append(section("7. Avaliação e resultados", styles))
    story.append(body(
        "A avaliação final foi realizada nas 36 imagens do conjunto de teste, contendo 108 objetos que não "
        "participaram do ajuste dos pesos nem da escolha do melhor checkpoint. As métricas globais são apresentadas "
        "a seguir.", styles
    ))
    story.append(styled_table([
        ["Métrica", "Resultado", "Interpretação"],
        ["Precisão", "97,7%", "poucas detecções incorretas"],
        ["Recall", "100,0%", "todos os objetos verdadeiros foram recuperados"],
        ["mAP@50", "99,5%", "excelente detecção no IoU mínimo de 0,50"],
        ["mAP@50–95", "80,9%", "boa localização sob limiares mais rigorosos"],
        ["Inferência", "≈ 5,1 ms/imagem", "medição local no Apple MPS"],
    ], [40 * mm, 35 * mm, 89 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(subsection("Resultados por classe", styles))
    story.append(styled_table([
        ["Classe", "Precisão", "Recall", "mAP@50", "mAP@50–95"],
        ["Dado", "98,9%", "100,0%", "99,5%", "99,5%"],
        ["Peão", "99,5%", "100,0%", "99,5%", "74,8%"],
        ["Ficha", "94,6%", "100,0%", "99,5%", "68,3%"],
    ], [34 * mm, 32 * mm, 32 * mm, 32 * mm, 34 * mm]))
    story.append(Spacer(1, 4 * mm))
    story.append(body(
        "O dado apresentou a localização mais estável porque sua geometria produz limites retangulares bem "
        "definidos. Peões e fichas mantiveram classificação correta no IoU 0,50, mas suas formas curvas, sombras "
        "e perspectiva tornam pequenas diferenças de caixa mais relevantes nos limiares altos usados pelo "
        "mAP@50–95.", styles
    ))
    story.append(figure(
        ROOT / "results" / "boardvision_test" / "confusion_matrix_normalized.png",
        "Figura 4 — Matriz de confusão normalizada no limiar de confiança 0,25. Fonte: avaliação do modelo (2026).",
        styles, max_height=92 * mm
    ))

    story.append(PageBreak())
    story.append(section("8. Análise qualitativa", styles))
    story.append(body(
        "As predições mostram que o modelo reconhece os três objetos sob diferentes combinações de cor, "
        "posição, escala, enquadramento e iluminação. Mesmo quando as peças aparecem próximas, as caixas são "
        "separadas corretamente na maioria dos exemplos. Os valores de confiança foram mais altos para os dados "
        "e moderados para peões e fichas, comportamento coerente com os resultados por classe.", styles
    ))
    story.append(figure(
        ROOT / "results" / "prediction_grid.jpg",
        "Figura 5 — Predições do melhor modelo em 12 imagens do conjunto de teste. Fonte: elaboração própria (2026).",
        styles, max_height=125 * mm
    ))
    story.append(section("9. Limitações e domain gap", styles))
    story.append(body(
        "Os números obtidos medem o desempenho em imagens sintéticas produzidas pela mesma família de cenas. "
        "Portanto, eles não comprovam diretamente a mesma qualidade em fotografias reais. Esse intervalo entre "
        "o domínio sintético e o real é chamado <i>domain gap</i>.", styles
    ))
    story.append(body(
        "Fotos reais podem incluir texturas, desgaste, reflexos, desfoque, lentes, fundos e oclusões que não foram "
        "simulados. Como próximos passos, o dataset pode receber texturas fotográficas, geometrias alternativas "
        "para cada classe, fundos mais complexos e oclusões controladas. Também seria importante criar um pequeno "
        "conjunto real anotado para medir o domain gap e decidir quais novas variações devem ser incluídas.", styles
    ))

    story.append(PageBreak())
    story.append(section("10. Instruções de uso", styles))
    story.append(body(
        "O repositório contém a cena do Blender, o script de geração, o dataset completo, os scripts de "
        "treinamento e avaliação, os pesos do melhor modelo, as figuras e este relatório. O README apresenta "
        "todos os comandos. O fluxo resumido é:", styles
    ))
    steps = [
        ["1", "Criar um ambiente Python e instalar requirements.txt."],
        ["2", "Executar generate_dataset.py pelo Blender em modo background."],
        ["3", "Rodar validate_dataset.py e conferir o JSON e a grade de anotações."],
        ["4", "Treinar com train_yolo.py; o melhor peso será copiado para models/best.pt."],
        ["5", "Avaliar com evaluate_yolo.py e consultar results/test_metrics.json."],
        ["6", "Usar predict.py para processar uma imagem, vídeo ou pasta."],
    ]
    story.append(styled_table([["Etapa", "Procedimento"]] + steps, [18 * mm, 146 * mm]))
    story.append(Spacer(1, 5 * mm))
    story.append(section("11. Conclusão", styles))
    story.append(body(
        "O BoardVision cumpriu o objetivo de integrar todas as etapas do desafio final. A cena e os objetos foram "
        "criados proceduralmente, as variações foram automatizadas, as caixas foram geradas sem anotação manual e "
        "o dataset foi validado antes do treinamento. O YOLOv8n atingiu mAP@50 de 99,5% no teste sintético, "
        "demonstrando que o conjunto contém informação suficiente para aprender as três classes propostas.", styles
    ))
    story.append(body(
        "O principal aprendizado foi perceber que o valor dos dados sintéticos não está apenas em produzir muitas "
        "imagens, mas em controlar a diversidade, manter as anotações corretas, separar adequadamente os conjuntos "
        "e interpretar as métricas considerando as limitações do domínio. O projeto ficou organizado e reproduzível "
        "para permitir novos ciclos de geração e treinamento.", styles
    ))
    story.append(section("Referências", styles))
    references = [
        "BLENDER FOUNDATION. <i>Blender Python API Documentation</i>. Disponível em: https://docs.blender.org/api/current/.",
        "ULTRALYTICS. <i>Object Detection Datasets Overview</i>. Disponível em: https://docs.ultralytics.com/datasets/detect/.",
        "ULTRALYTICS. <i>Model Training with Ultralytics YOLO</i>. Disponível em: https://docs.ultralytics.com/modes/train/.",
        "KELLY, Adam. Tutoriais do curso sobre geração de dados sintéticos, Blender e visão computacional.",
    ]
    for item in references:
        story.append(Paragraph("• " + item, styles["BodySmall"]))
    story.append(Spacer(1, 5 * mm))
    repo_url = "https://github.com/Fefdiniz11/FastCamp-Dados-Sinteticos/tree/main/ProjetoFinal"
    repo_box = Table([[Paragraph(
        f"<b>Repositório do projeto:</b><br/><link href='{repo_url}' color='#007C82'>{repo_url}</link>",
        ParagraphStyle("Repo", parent=styles["BodyCustom"], alignment=TA_CENTER)
    )]], colWidths=[160 * mm])
    repo_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SKY),
        ("BOX", (0, 0), (-1, -1), 0.8, TEAL),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.append(repo_box)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build_report()
