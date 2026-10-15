"""
experimento_baseline.py — Fase 2: baseline (NSGA-II) no benchmark do projeto.

Rode com:   python3 experimento_baseline.py      (~5 min)

Protocolo (protocolo.py): bbob-biobj, 55 funções x D = 5, 10, 20 x
instâncias 1 a 15, orçamento 30 x D, população 20.

Roda dois algoritmos com o observador do COCO ligado:
  1. NSGA-II (o baseline, variante A);
  2. busca aleatória com o mesmo orçamento (o "piso" do benchmark, em
     ../fase2b_benchmark/busca_aleatoria.py: o NSGA-II precisa ser melhor que
     sortear soluções ao acaso).

Saídas:
  exdata/                        dados brutos do COCO (não vão para o git)
  ppdata/                        análise completa do cocopp (abra index.html)
  resultados/bbob_finais.csv     indicador final de cada execução
  resultados/bbob_resumo.txt     resumo por dimensão e por grupo de funções
  resultados/B1_ecdf_*.png       curvas ECDF do COCO (NSGA-II x aleatória x best 2016)
  resultados/B2_convergencia_bbob.png   mediana de delta_HV ao longo do orçamento
"""

import csv
import glob
import os
import shutil
import subprocess
import sys
import time
from collections import defaultdict

import numpy as np

from nsga2_baseline import rodar_nsga2          # já aponta para ../fase2b_benchmark
from busca_aleatoria import busca_aleatoria
from coco_utils import rodar_no_bbob, ler_resultados_finais
from funcoes_bbob import grupo_da_funcao
from protocolo import PROTOCOLO_BBOB as P, orcamento, seed_da_instancia

PASTA = "resultados"
os.makedirs(PASTA, exist_ok=True)
linhas = []


def log(msg=""):
    print(msg)
    linhas.append(msg)


# ---------------------------------------------------------------------------
# Os dois otimizadores
# ---------------------------------------------------------------------------
def nsga2(problema, orc, seed):
    rodar_nsga2(problema=problema, tam_pop=P["tam_pop"], n_inicial=P["n_inicial"],
                orcamento=orc, seed=seed)


# ---------------------------------------------------------------------------
# 1) Rodar
# ---------------------------------------------------------------------------
config = dict(funcoes=P["funcoes"], dimensoes=P["dimensoes"],
              instancias=P["instancias"], orcamento=orcamento,
              seed=seed_da_instancia)
n_exec = len(P["funcoes"]) * len(P["dimensoes"]) * len(P["instancias"])
log("=" * 70)
log(f"Baseline no bbob-biobj: {len(P['funcoes'])} funções x D={P['dimensoes']} x "
    f"{len(P['instancias'])} instâncias = {n_exec} execuções por algoritmo")
log(f"Orçamento: {P['orcamento_por_dimensao']} x D | população {P['tam_pop']} | "
    f"amostra inicial {P['n_inicial']}")
log("=" * 70)

tempos = {}
for nome, otimizador in [("NSGA-II", nsga2), ("Aleatoria", busca_aleatoria)]:
    print(f"\nRodando {nome}...")
    t0 = time.perf_counter()
    rodar_no_bbob(otimizador, nome, **config)
    tempos[nome] = time.perf_counter() - t0
    log(f"{nome}: {tempos[nome]:.0f} s no total")

# ---------------------------------------------------------------------------
# 2) Ler o indicador final de cada execução
# ---------------------------------------------------------------------------
res = {nome: ler_resultados_finais(os.path.join("exdata", nome))
       for nome in ("NSGA-II", "Aleatoria")}
for nome, r in res.items():
    assert len(r) == n_exec, f"{nome}: esperava {n_exec} execuções, li {len(r)}"
    for x in r:
        assert x["avaliacoes"] == orcamento(x["dimensao"]), x

with open(f"{PASTA}/bbob_finais.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["algoritmo", "funcao", "dimensao", "instancia", "avaliacoes", "delta_hv"])
    for nome, r in res.items():
        for x in sorted(r, key=lambda x: (x["dimensao"], x["funcao"], x["instancia"])):
            w.writerow([nome, x["funcao"], x["dimensao"], x["instancia"],
                        x["avaliacoes"], f"{x['delta_hv']:.6g}"])

chave = lambda x: (x["funcao"], x["dimensao"], x["instancia"])
nsga = {chave(x): x["delta_hv"] for x in res["NSGA-II"]}
alea = {chave(x): x["delta_hv"] for x in res["Aleatoria"]}

# ---------------------------------------------------------------------------
# 3) Resumo por dimensão
# ---------------------------------------------------------------------------
log("")
log("delta_HV final (diferença para o HV de referência do COCO; menor é melhor)")
log(f"{'D':>3} | {'orç.':>5} | {'NSGA-II mediana':>16} | {'Aleatória mediana':>18} | "
    f"{'NSGA-II melhor em':>18} | {'alvo 0.1 (NSGA-II)':>19}")
for d in P["dimensoes"]:
    ks = [k for k in nsga if k[1] == d]
    a = np.array([nsga[k] for k in ks])
    b = np.array([alea[k] for k in ks])
    log(f"{d:>3} | {orcamento(d):>5} | {np.median(a):>16.3f} | {np.median(b):>18.3f} | "
        f"{100 * np.mean(a < b):>17.0f}% | {100 * np.mean(a <= 0.1):>18.0f}%")

# Teste de sinal pareado (mesma função/dimensão/instância) NSGA-II x aleatória
from scipy.stats import wilcoxon
a_all = np.array([nsga[k] for k in nsga])
b_all = np.array([alea[k] for k in nsga])
p = wilcoxon(a_all, b_all, alternative="less").pvalue
log(f"Wilcoxon pareado (NSGA-II < aleatória), todas as {len(a_all)} execuções: p = {p:.1e}")

# ---------------------------------------------------------------------------
# 4) Resumo por grupo de funções (D = 10)
# ---------------------------------------------------------------------------
grupo_da_funcao = grupo_da_funcao()

log("")
log("Por grupo de funções, D = 10 (mediana de delta_HV sobre funções x instâncias)")
grupos = defaultdict(list)
for k, v in nsga.items():
    if k[1] == 10:
        grupos[grupo_da_funcao[k[0]]].append((v, alea[k]))
for g in dict.fromkeys(grupo_da_funcao.values()):
    v = np.array(grupos[g])
    log(f"  {g:<46} NSGA-II {np.median(v[:, 0]):6.3f} | aleatória {np.median(v[:, 1]):6.3f}")

with open(f"{PASTA}/bbob_resumo.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")

# ---------------------------------------------------------------------------
# 5) Análise oficial do COCO (curvas ECDF)
# ---------------------------------------------------------------------------
print("\nGerando a análise do cocopp (pode levar alguns minutos)...")
if os.path.exists("ppdata"):
    shutil.rmtree("ppdata")
subprocess.run([sys.executable, "-m", "cocopp", "-o", "ppdata",
                "exdata/NSGA-II", "exdata/Aleatoria"],
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# Copia as curvas ECDF agregadas (todas as funções) de cada dimensão
try:
    import cairosvg
    for d in P["dimensoes"]:
        achados = glob.glob(f"ppdata/**/pprldmany_{d:02d}D_noiselessall.svg", recursive=True)
        if achados:
            cairosvg.svg2png(url=achados[0], write_to=f"{PASTA}/B1_ecdf_{d:02d}D.png",
                             output_width=900)
    print("Curvas ECDF copiadas para resultados/")
except ImportError:
    print("Instale cairosvg para copiar as curvas em PNG; elas estão em ppdata/ (SVG).")
print("Análise completa: abra ppdata/index.html no navegador.")

# ---------------------------------------------------------------------------
# 6) Curvas de convergência dentro do orçamento (mais fáceis de ler)
# ---------------------------------------------------------------------------
from grafico_convergencia import gerar
print("Curva de convergência salva em", gerar())
