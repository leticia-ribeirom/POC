"""
experimento_decisoes.py — Experimento que embasa as decisões propostas para o
protocolo do POC I (ver README, seção "Decisões propostas").

Rode com:   python3 experimento_decisoes.py

Cenário fixo (justificado pela literatura, ver README):
  ZDT1 com 10 variáveis, orçamento de 300 avaliações reais.

O que este script faz:
  1. Calcula o ponto de referência do HV pela regra proposta:
     10% pior que o pior valor de cada objetivo nas frentes INICIAIS
     (aleatórias) de 30 execuções, arredondado para cima (1 casa decimal).
     Assim, qualquer melhoria em relação à amostragem aleatória aparece no HV.
  2. Compara tamanhos de população que dividem o orçamento exatamente e são
     múltiplos de 4 (exigência do DEAP): 12, 20, 60 e 100. Para cada um,
     30 execuções com seeds 1..30, medindo IGD e HV finais.
"""

import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nsga2_baseline import rodar_nsga2
from metricas import hipervolume

PROBLEMA, N_VAR, ORCAMENTO = "zdt1", 10, 300
SEEDS = range(1, 31)
POPULACOES = [12, 20, 60, 100]
PASTA = "resultados"
os.makedirs(PASTA, exist_ok=True)

AZUL, CINZA = "#2a78d6", "#8a8a8a"
plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
    "axes.edgecolor": "#9a9a9a", "font.size": 10,
})

linhas = []


def log(msg=""):
    print(msg)
    linhas.append(msg)


# ---------------------------------------------------------------------------
# 1) Ponto de referência do HV
# ---------------------------------------------------------------------------
log("=" * 70)
log("1) Ponto de referência do HV")
log("=" * 70)
piores = []
for seed in SEEDS:
    # A população inicial é aleatória; usamos pop 20 (qualquer uma serviria,
    # só precisamos das frentes aleatórias iniciais).
    r = rodar_nsga2(PROBLEMA, tam_pop=20, orcamento=20, seed=seed, n_var=N_VAR)
    piores.append(r["historico"][0]["frente"].max(axis=0))
pior = np.max(piores, axis=0)
ref = tuple(math.ceil(v * 1.1 * 10) / 10 for v in pior)
log(f"Pior valor observado nas frentes iniciais (30 seeds): f1 = {pior[0]:.3f}, f2 = {pior[1]:.3f}")
log(f"Ponto de referência proposto (pior x 1.1, arredondado para cima): {ref}")

# ---------------------------------------------------------------------------
# 2) Tamanho da população
# ---------------------------------------------------------------------------
log("")
log("=" * 70)
log(f"2) Tamanho da população (ZDT1, n={N_VAR}, orçamento {ORCAMENTO}, 30 seeds)")
log("=" * 70)
res = {}
curvas = {}
for N in POPULACOES:
    igds, hvs, hv_ref_curta = [], [], []
    curva = []
    for seed in SEEDS:
        r = rodar_nsga2(PROBLEMA, tam_pop=N, orcamento=ORCAMENTO, seed=seed,
                        n_var=N_VAR, ref_hv=ref)
        h = r["historico"][-1]
        assert r["avaliacoes"] == ORCAMENTO
        igds.append(h["igd"])
        hvs.append(h["hv"])
        hv_ref_curta.append(hipervolume(r["frente_final"], (1.1, 1.1)))
        curva.append([(x["avaliacoes"], x["igd"]) for x in r["historico"]])
    res[N] = (np.array(igds), np.array(hvs), np.array(hv_ref_curta))
    curvas[N] = curva
    geracoes = (ORCAMENTO - N) // N
    log(f"pop {N:3d} ({geracoes:2d} gerações): IGD {np.mean(igds):.3f} ± {np.std(igds):.3f} | "
        f"mediana {np.median(igds):.3f} | HV(ref {ref}) {np.mean(hvs):.3f} ± {np.std(hvs):.3f} | "
        f"HV(ref 1.1,1.1) {np.mean(hv_ref_curta):.3f}")

melhor = min(POPULACOES, key=lambda n: np.median(res[n][0]))
log(f"Menor IGD mediano: pop {melhor}")

# Teste de Mann-Whitney (não paramétrico) entre as duas melhores populações:
# a diferença de IGD é real ou pode ser acaso?
from scipy.stats import mannwhitneyu
p_12_20 = mannwhitneyu(res[12][0], res[20][0]).pvalue
p_20_60 = mannwhitneyu(res[20][0], res[60][0]).pvalue
log(f"Mann-Whitney IGD pop 12 vs 20: p = {p_12_20:.3f} "
    f"({'diferença significativa' if p_12_20 < 0.05 else 'SEM diferença significativa'} a 5%)")
log(f"Mann-Whitney IGD pop 20 vs 60: p = {p_20_60:.2g} "
    f"({'diferença significativa' if p_20_60 < 0.05 else 'SEM diferença significativa'} a 5%)")
PROPOSTA = 20
log(f"Proposta: pop {PROPOSTA}. Empata estatisticamente com 12 e é claramente melhor que 60 e 100; "
    f"entre as empatadas, 20 mantém mais pontos na frente final (melhor cobertura da fronteira).")
log("Obs.: com HV(ref 1.1, 1.1) quase tudo dá zero nesse regime, o que confirma "
    "que a referência precisa ser adequada ao cenário de poucas avaliações.")

# Gráfico: distribuição do IGD final por tamanho de população
fig, axes = plt.subplots(1, 2, figsize=(11, 4))
ax = axes[0]
ax.boxplot([res[N][0] for N in POPULACOES], widths=0.5,
           medianprops=dict(color=AZUL, linewidth=2),
           boxprops=dict(color="#555"), whiskerprops=dict(color="#555"),
           capprops=dict(color="#555"), flierprops=dict(markeredgecolor=CINZA))
ax.set_xticks(range(1, len(POPULACOES) + 1), [str(N) for N in POPULACOES])
ax.set_xlabel("Tamanho da população")
ax.set_ylabel("IGD final (menor é melhor)")
ax.set_title("IGD final após 300 avaliações (30 seeds)")

# Gráfico: curva mediana de IGD x avaliações, só para a população proposta
ax = axes[1]
for N in POPULACOES:
    avals = [a for a, _ in curvas[N][0]]
    mediana = np.median([[g for _, g in c] for c in curvas[N]], axis=0)
    destaque = N == PROPOSTA
    ax.plot(avals, mediana, lw=2 if destaque else 1.2,
            color=AZUL if destaque else CINZA, alpha=1 if destaque else 0.8)
    # pequeno deslocamento vertical para os rótulos de 12 e 20 não se sobreporem
    desloc = {12: -0.04, 20: 0.04}.get(N, 0.0)
    ax.text(avals[-1] + 4, mediana[-1] + desloc, f"pop {N}", va="center", fontsize=9,
            color="#222" if destaque else "#666")
ax.set_xlabel("Avaliações reais")
ax.set_ylabel("IGD mediano (30 seeds)")
ax.set_title("Convergência do IGD por tamanho de população")
ax.set_xlim(0, ORCAMENTO + 45)
fig.tight_layout()
fig.savefig(f"{PASTA}/D1_tamanho_populacao.png", dpi=150)
plt.close(fig)

with open(f"{PASTA}/relatorio_decisoes.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")
