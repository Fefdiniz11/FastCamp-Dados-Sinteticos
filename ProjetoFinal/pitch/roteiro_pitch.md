# Roteiro do pitch — BoardVision

Duração prevista: aproximadamente 2 minutos e 30 segundos.

## 1. Abertura

Olá, eu sou Fernanda Diniz e este é o BoardVision, meu projeto final do curso de Dados Sintéticos. O objetivo foi construir um pipeline completo de visão computacional, começando no Blender e terminando em um modelo capaz de detectar três peças de jogos: dado, peão e ficha.

## 2. Problema

Treinar detectores normalmente exige muitas fotografias e anotações manuais. Isso demanda tempo e pode produzir um conjunto pouco variado. A proposta do BoardVision foi substituir essa etapa por uma cena sintética controlada, na qual a posição e os limites dos objetos já são conhecidos pelo simulador.

## 3. Solução

Os três objetos foram construídos proceduralmente no Blender, sem depender de modelos externos. Um script em Python com a API bpy randomiza posição, rotação, escala, cor, material, fundo, câmera e iluminação. Para cada cena, o mesmo script renderiza a imagem e projeta a geometria 3D na câmera, gerando automaticamente as bounding boxes no formato YOLO.

## 4. Dataset

O dataset final possui 240 imagens com resolução de 416 por 416 pixels e 720 objetos anotados. Foram usadas 168 imagens para treino, 36 para validação e 36 para teste. As três classes ficaram balanceadas. Um validador automático conferiu todos os pares de imagem e rótulo e não encontrou erros.

## 5. Treinamento e resultados

O detector escolhido foi o YOLOv8n, treinado por 20 épocas com transferência de aprendizado. No conjunto de teste separado, o modelo alcançou precisão de 97,7%, recall de 100%, mAP cinquenta de 99,5% e mAP de cinquenta a noventa e cinco de 80,9%. As predições mostram boa identificação mesmo com mudanças de cor, luz, posição e escala.

## 6. Diferenciais e encerramento

Os principais diferenciais são a reprodução completa por scripts, as anotações sem trabalho manual e a entrega de todos os artefatos: cena do Blender, dataset, código, pesos treinados, métricas e documentação. A principal limitação é o domain gap, porque o teste ainda é sintético. Como próximo passo, eu incluiria texturas e fundos reais e avaliaria o modelo em fotografias. O projeto demonstra, de ponta a ponta, como dados sintéticos podem acelerar a criação de uma solução de visão computacional. Obrigada.
