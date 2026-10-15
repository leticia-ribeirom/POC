"""
figura_funil.py — Figura do fluxo de uma geração do método, em formato de funil.

Rode com:   python3 figura_funil.py      (precisa de cairosvg)
Saída:      F1_funil_metodo.png  (e .svg), nesta pasta

Mostra a ideia central do projeto: muitos candidatos entram no topo
(cruzamento e mutação + LLM), o Random Forest filtra, e só 20 gastam
avaliação real. Os números seguem protocolo.py.
"""

import os
import sys

import cairosvg

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
# a pasta do benchmark é a que tem coco_utils.py e protocolo.py (qualquer nome)
for _nome in sorted(os.listdir(RAIZ)):
    _p = os.path.join(RAIZ, _nome)
    if os.path.isfile(os.path.join(_p, "coco_utils.py")) and os.path.isfile(os.path.join(_p, "protocolo.py")):
        sys.path.insert(0, _p)
        break
from protocolo import N_CANDIDATOS_OPCOES, PROTOCOLO_BBOB

W, H = 1080, 720
C = 460  # centro horizontal
FONTE = "DejaVu Sans, Arial, sans-serif"

# (preenchimento, borda, título, subtítulo) — rampas claras, legíveis impressas
CINZA = ("#F1EFE8", "#5F5E5A", "#2C2C2A", "#5F5E5A")
ROXO = ("#EEEDFE", "#534AB7", "#26215C", "#534AB7")
VERDE = ("#E1F5EE", "#0F6E56", "#04342C", "#0F6E56")
CORAL = ("#FAECE7", "#993C1D", "#4A1B0C", "#993C1D")

N = PROTOCOLO_BBOB["tam_pop"]
cands = ", ".join(map(str, N_CANDIDATOS_OPCOES[:-1])) + f" ou {N_CANDIDATOS_OPCOES[-1]}"

el = []


def textos(cx, cy, titulo, sub, cor):
    el.append(f'<text x="{cx}" y="{cy - 9}" text-anchor="middle" font-family="{FONTE}" '
              f'font-size="17" font-weight="bold" fill="{cor[2]}">{titulo}</text>')
    el.append(f'<text x="{cx}" y="{cy + 15}" text-anchor="middle" font-family="{FONTE}" '
              f'font-size="14" fill="{cor[3]}">{sub}</text>')


def caixa(x0, x1, y0, h, cor, titulo, sub):
    el.append(f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{h}" rx="6" '
              f'fill="{cor[0]}" stroke="{cor[1]}" stroke-width="1.2"/>')
    textos((x0 + x1) / 2, y0 + h / 2, titulo, sub, cor)


def trapezio(topo, base, y0, h, cor, titulo, sub):
    """topo/base = meia-largura; desenha o degrau do funil."""
    pts = f"{C - topo},{y0} {C + topo},{y0} {C + base},{y0 + h} {C - base},{y0 + h}"
    el.append(f'<polygon points="{pts}" fill="{cor[0]}" stroke="{cor[1]}" stroke-width="1.2" '
              f'stroke-linejoin="round"/>')
    textos(C, y0 + h / 2, titulo, sub, cor)


def seta(d, cor="#5F5E5A"):
    el.append(f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="1.6" '
              f'marker-end="url(#seta_{cor[1:]})"/>')


def rotulo(y, linhas, forte=False):
    for i, t in enumerate(linhas):
        el.append(f'<text x="850" y="{y + i * 20}" font-family="{FONTE}" font-size="15" '
                  f'font-weight="{"bold" if (forte and i == 0) else "normal"}" fill="#444441">{t}</text>')


# --- População e as duas fontes de candidatos ---
caixa(300, 620, 30, 60, CINZA, "População atual", f"{N} soluções + arquivo de avaliações")
seta("M 400 90 V 110 H 300 V 126")
seta("M 520 90 V 110 H 620 V 126")
caixa(160, 440, 130, 60, CINZA, "Cruzamento e mutação", f"{cands} filhos, às cegas")
caixa(480, 760, 130, 60, ROXO, "LLM (Claude)", "propõe olhando o histórico")
seta("M 300 190 V 226")
seta("M 620 190 V 226", "#534AB7")

# --- O funil ---
trapezio(360, 300, 230, 70, CINZA, "Grupo de candidatos", "todos tratados da mesma forma")
rotulo(258, [f"{cands}", "+ propostas do LLM"], forte=True)
seta(f"M {C} 300 V 312")
trapezio(300, 230, 316, 70, VERDE, "Random Forest prevê", "estima f1 e f2 de cada um, sem custo")
seta(f"M {C} 386 V 398")
trapezio(230, 160, 402, 70, VERDE, "Pré-seleção", f"fica com os {N} mais promissores")
rotulo(442, [f"{N} escolhidos"], forte=True)
seta(f"M {C} 472 V 492")
caixa(270, 650, 496, 60, CORAL, "Avaliação real (bbob-biobj)", f"{N} avaliações: gasta orçamento")
rotulo(531, [f"{N} avaliações reais"], forte=True)
seta(f"M {C} 556 V 576")
caixa(270, 650, 580, 60, CINZA, "Sobrevivência NSGA-II e arquivo", f"{N} melhores; RF e LLM aprendem")
seta("M 270 610 H 40 V 60 H 296")

# --- Legenda ---
for x, (cor, nome) in zip([150, 300, 420, 680],
                         [(CINZA, "NSGA-II"), (ROXO, "LLM"), (VERDE, "surrogate (Random Forest)"),
                          (CORAL, "gasta orçamento")]):
    el.append(f'<rect x="{x}" y="672" width="16" height="16" rx="3" fill="{cor[0]}" '
              f'stroke="{cor[1]}" stroke-width="1"/>')
    el.append(f'<text x="{x + 24}" y="685" font-family="{FONTE}" font-size="14" '
              f'fill="#444441">{nome}</text>')

marcadores = "".join(
    f'<marker id="seta_{c[1:]}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" '
    f'markerHeight="7" orient="auto-start-reverse"><path d="M2 1L8 5L2 9" fill="none" '
    f'stroke="{c}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></marker>'
    for c in ("#5F5E5A", "#534AB7"))

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
       f'<defs>{marcadores}</defs><rect width="{W}" height="{H}" fill="white"/>'
       + "".join(el) + "</svg>")

with open(os.path.join(AQUI, "F1_funil_metodo.svg"), "w", encoding="utf-8") as f:
    f.write(svg)
cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=os.path.join(AQUI, "F1_funil_metodo.png"),
                 output_width=W * 2)
print("salvo em F1_funil_metodo.png (pasta documentos/figuras)")
