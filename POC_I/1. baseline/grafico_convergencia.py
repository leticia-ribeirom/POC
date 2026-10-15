"""
grafico_convergencia.py — Gráfico B2: curvas de convergência no bbob-biobj.

Rode com:   python3 grafico_convergencia.py   (depois de experimento_baseline.py)

Para cada dimensão, mostra a MEDIANA do indicador do COCO (delta_HV, menor é
melhor) ao longo das avaliações, sobre todas as funções e instâncias, para
cada algoritmo em exdata/. A faixa clara vai do quartil 25% ao 75%.

É uma leitura mais direta que a ECDF do cocopp: mostra só o que acontece
DENTRO do orçamento (30 x D).
"""

import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "fase2b_benchmark"))
from protocolo import PROTOCOLO_BBOB as P, orcamento

CORES = {"NSGA-II": "#2a78d6", "Aleatoria": "#eb6834"}
ROTULOS = {"NSGA-II": "NSGA-II (baseline)", "Aleatoria": "Busca aleatória"}
_NOME_DAT = re.compile(r"bbob-biobj_f(\d+)_d(\d+)_hyp\.dat$")

plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
    "axes.edgecolor": "#9a9a9a", "font.size": 10,
})


def trajetorias(pasta, dim, funcao=None):
    """Lista de trajetórias [(avaliacao, delta_hv), ...], uma por execução.
    Se `funcao` for dada, lê só as execuções dessa função."""
    trajs = []
    for raiz, _, arquivos in os.walk(pasta):
        for nome in arquivos:
            m = _NOME_DAT.search(nome)
            if not m or int(m.group(2)) != dim:
                continue
            if funcao is not None and int(m.group(1)) != funcao:
                continue
            atual = None
            with open(os.path.join(raiz, nome), encoding="utf-8") as f:
                for linha in f:
                    if linha.startswith("% instance"):
                        if atual:
                            trajs.append(atual)
                        atual = []
                    elif not linha.startswith("%") and linha.strip():
                        a, v = linha.split()[:2]
                        atual.append((int(a), float(v)))
            if atual:
                trajs.append(atual)
    return trajs


def valor_em(traj, avaliacao):
    """Indicador depois de `avaliacao` avaliações (o COCO grava só quando
    melhora, então vale o último registro até ali)."""
    v = np.nan
    for a, x in traj:
        if a > avaliacao:
            break
        v = x
    return v


def gerar(pasta_dados="exdata", saida="resultados/B2_convergencia_bbob.png"):
    algoritmos = [a for a in ("NSGA-II", "Aleatoria")
                  if os.path.isdir(os.path.join(pasta_dados, a))]
    dims = P["dimensoes"]
    fig, axes = plt.subplots(1, len(dims), figsize=(4.2 * len(dims), 3.8), sharey=True)
    for ax, d in zip(axes, dims):
        pontos = np.unique(np.linspace(d, orcamento(d), 60).astype(int))
        for alg in algoritmos:
            trajs = trajetorias(os.path.join(pasta_dados, alg), d)
            M = np.array([[valor_em(t, a) for a in pontos] for t in trajs])
            med = np.nanmedian(M, axis=0)
            q1, q3 = np.nanpercentile(M, 25, axis=0), np.nanpercentile(M, 75, axis=0)
            x = pontos / d
            ax.fill_between(x, q1, q3, color=CORES[alg], alpha=0.15, lw=0)
            ax.plot(x, med, color=CORES[alg], lw=2, label=ROTULOS[alg])
            ax.text(x[-1] + 0.4, med[-1], f"{med[-1]:.2f}", va="center",
                    fontsize=9, color="#333")
        ax.set_title(f"D = {d}  (orçamento {orcamento(d)})")
        ax.set_xlabel("avaliações reais / D")
        ax.set_xlim(0, P["orcamento_por_dimensao"] + 4)
        ax.set_yscale("log")
        ax.set_yticks([0.1, 0.2, 0.3, 0.5, 1.0])
        ax.set_yticklabels(["0.1", "0.2", "0.3", "0.5", "1"])
    axes[0].set_ylabel("delta_HV do COCO (mediana; menor é melhor)")
    axes[0].legend(frameon=False, loc="upper right")
    fig.suptitle("Baseline no bbob-biobj: 55 funções x 15 instâncias por dimensão "
                 "(faixa = quartis 25%–75%)", y=1.02)
    fig.tight_layout()
    fig.savefig(saida, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return saida


if __name__ == "__main__":
    print("Gráfico salvo em", gerar())
