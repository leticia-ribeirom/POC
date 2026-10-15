"""
grafico_populacao.py — Gráfico P1: tamanho da população no bbob-biobj.

Rode com:   python3 grafico_populacao.py
(lê resultados/bbob_populacao.txt, gerado por experimento_populacao.py)
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

with open("resultados/bbob_populacao.txt", encoding="utf-8") as f:
    linhas = f.read().splitlines()
cab = linhas[1].split("|")[2:]
pops = [int(c.replace("pop", "").strip()) for c in cab]
dados = {}
for linha in linhas[2:]:
    if not linha.strip() or not linha.strip()[0].isdigit():
        break
    partes = [p.strip() for p in linha.split("|")]
    dados[int(partes[0])] = (int(partes[1]), [float(v) for v in partes[2:]])

CORES = {5: "#2a78d6", 10: "#eb6834", 20: "#1baf7a"}
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
                     "axes.edgecolor": "#9a9a9a", "font.size": 10})
fig, ax = plt.subplots(figsize=(7, 4.2))
ax.axvline(20, color="#8a8a8a", lw=1, ls="--", zorder=0)
ax.text(21, 0.50, "população\nescolhida (20)", color="#555", fontsize=9, va="top")
for d, (orc, med) in dados.items():
    ax.plot(pops, med, marker="o", ms=5, lw=2, color=CORES[d])
    desloc = {20: 0.012, 10: -0.012}.get(d, 0.0)   # evita sobrepor D = 10 e D = 20
    ax.text(pops[-1] * 1.08, med[-1] + desloc, f"D = {d} ({orc} aval.)", va="center",
            fontsize=9, color="#333")
ax.set_xscale("log")
ax.set_xticks(pops)
ax.set_xticklabels([str(p) for p in pops])
ax.minorticks_off()
ax.set_xlim(7, 260)
ax.set_xlabel("tamanho da população (escala log)")
ax.set_ylabel("delta_HV final (mediana; menor é melhor)")
ax.set_title("Populações maiores pioram o resultado com orçamento de 30 × D", fontsize=11)
fig.tight_layout()
fig.savefig("resultados/P1_populacao_bbob.png", dpi=150)
print("salvo em resultados/P1_populacao_bbob.png")
