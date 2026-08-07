# Projeto Final — Detecção de peças de jogos de tabuleiro com dados sintéticos

O projeto apresenta um pipeline de visão computacional que gera um dataset sintético no Blender, cria automaticamente anotações no formato YOLO, treina um modelo YOLOv8n e avalia seu desempenho na detecção de três peças de jogos de tabuleiro: `dado`, `peão` e `ficha`.

![Predições do modelo](results/prediction_grid.jpg)

## Dataset

Os objetos e a cena foram criados no Blender. O script varia posição, orientação, escala, cor, fundo, câmera e iluminação a cada renderização. Cada imagem possui os três objetos e suas respectivas bounding boxes.

O dataset contém **240 imagens** de **416 × 416 pixels** e **720 objetos anotados**.

| Divisão | Imagens | Objetos |
|---|---:|---:|
| Treino | 168 | 504 |
| Validação | 36 | 108 |
| Teste | 36 | 108 |
| **Total** | **240** | **720** |

As anotações seguem o formato YOLO: `classe x_centro y_centro largura altura`, com valores normalizados entre 0 e 1.

Foi utilizado o modelo **YOLOv8n**, iniciado com pesos pré-treinados e ajustado ao dataset sintético.

- Épocas: 20
- Tamanho das imagens: 416 × 416
- Batch: 16
- Otimizador: AdamW
- Taxa de aprendizado inicial: 0,001
- Dispositivo utilizado: Apple MPS

O melhor peso treinado está em `models/best.pt`.

## Resultados

A avaliação foi realizada no conjunto de teste, composto por 36 imagens e 108 objetos.

| Métrica | Resultado |
|---|---:|
| Precisão | **94,76%** |
| Recall | **99,51%** |
| mAP@50 | **98,84%** |
| mAP@50–95 | **82,13%** |

Resultados por classe:

| Classe | Precisão | Recall | mAP@50 | mAP@50–95 |
|---|---:|---:|---:|---:|
| Dado | 97,52% | 100,00% | 99,50% | 97,96% |
| Peão | 92,09% | 100,00% | 99,07% | 81,09% |
| Ficha | 94,66% | 98,54% | 97,95% | 67,34% |

![Curvas do treinamento](results/boardvision_train/results.png)

## Estrutura do projeto

```text
ProjetoFinal/
├── blender/
│   ├── ProjetoFinal.blend
│   └── generate_dataset.py
├── dataset/
│   ├── images/{train,val,test}/
│   ├── labels/{train,val,test}/
│   ├── data.yaml
│   ├── metadata.jsonl
│   └── summary.json
├── models/
│   └── best.pt
├── training/
│   ├── train_yolo.py
│   ├── evaluate_yolo.py
│   └── predict.py
├── results/
├── README.md
└── requirements.txt
```

## Como executar

### 1. Preparar o ambiente Python

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Gerar o dataset no Blender

Abra `blender/ProjetoFinal.blend` no Blender. Na área **Scripting**, abra o arquivo `blender/generate_dataset.py` e selecione **Run Script**. O dataset será criado na pasta `dataset/`.

### 3. Treinar o modelo

```bash
python training/train_yolo.py --epochs 20 --imgsz 416 --batch 16
```

### 4. Avaliar o modelo

```bash
python training/evaluate_yolo.py --imgsz 416 --batch 16 --samples 12
```

As métricas são salvas em `results/test_metrics.json` e as imagens com predições em `results/predictions/`.

### 5. Testar outra imagem

```bash
python training/predict.py caminho/para/imagem.png --conf 0.25
```

## Limitação

O modelo foi treinado e testado apenas com imagens sintéticas produzidas no Blender. Por isso, os resultados apresentados não garantem o mesmo desempenho em fotografias reais, devido às diferenças entre os dois domínios.

## Tecnologias utilizadas

- Blender e API Python `bpy`
- Python
- Ultralytics YOLOv8
- PyTorch
