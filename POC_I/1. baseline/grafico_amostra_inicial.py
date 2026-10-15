"""
grafico_amostra_inicial.py — Gráfico A1: tamanho da amostra inicial no bbob-biobj.

Rode com:   python3 grafico_amostra_inicial.py
(lê resultados/bbob_amostra_inicial.txt, gerado por experimento_amostra_inicial.py)
"""

import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

with open("resultados/bbob_amostra_inicial.txt", encoding="utf-8") as f:
    linhas = f.read().splitlines()
nomes = [c.strip() for c in linhas[1].split("|")[2:]]
dados = {}
for linha in linhas[2:]:
    if not linha.strip() or not linha.strip()[0].isdigit():
        break
    partes = [p.strip() for p in linha.split("|")]
    vals = [re.match(r"([\d.]+) \(amostra\s+(\d+)\)", c).groups() for c in partes[2:]]
    dados[int(partes[0])] = (int(partes[1]), [float(v) for v, _ in vals], [int(a) for _, a in vals])

CORES = ["#2a78d6", "#eb6834", "#1baf7a"]
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
                     "axes.edgecolor": "#9a9a9a", "font.size": 10})
fig, ax = plt.subplots(figsize=(7, 4.2))
largura = 0.26
xs = np.arange(len(dados))
for j, (nome, cor) in enumerate(zip(nomes, CORES)):
    meds = [dados[d][1][j] for d in dados]
    barras = ax.bar(xs + (j - 1) * largura, meds, largura, color=cor,
                    label={"20": "20 (clássico)", "40": "40", "11D-1": "11D − 1 (K-RVEA)"}[nome])
    for b, d in zip(barras, dados):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.004,
                f"{dados[d][1][j]:.3f}\n({dados[d][2][j]})", ha="center", va="bottom", fontsize=7.5)
ax.set_xticks(xs)
ax.set_xticklabels([f"D = {d}\n({dados[d][0]} aval.)" for d in dados])
ax.set_ylim(0, 0.40)
ax.set_axisbelow(True)
ax.set_ylabel("delta_HV final (mediana; menor é melhor)")
ax.set_title("Amostra inicial no NSGA-II puro: diferenças pequenas", fontsize=11)
ax.legend(frameon=False, title="amostra inicial", ncol=3, loc="upper left", fontsize=9)
fig.tight_layout()
fig.savefig("resultados/A1_amostra_inicial_bbob.png", dpi=150)
print("salvo em resultados/A1_amostra_inicial_bbob.png")
