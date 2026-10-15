"""
experimento_amostra_inicial.py — Tamanho da amostra inicial no bbob-biobj.

Rode com:   python3 experimento_amostra_inicial.py          (~6 min)
            python3 experimento_amostra_inicial.py --so-analise

A amostra inicial são as soluções aleatórias avaliadas antes de a evolução
começar. Ela gasta orçamento, e na Fase 3 é o primeiro conjunto de treino do
Random Forest. Este script mede o efeito dela no NSGA-II PURO (população 20),
no protocolo do projeto (55 funções x D = 5, 10, 20 x 15 instâncias, 30 x D):

  20        o NSGA-II clássico (amostra = população)
  40        o dobro
  11D - 1   a regra do K-RVEA (CHUGH et al., 2018): 54, 109 e 219 em D = 5, 10, 20

Saída: resultados/bbob_amostra_inicial.txt
"""

import os
import sys

import numpy as np
from scipy.stats import wilcoxon

from nsga2_baseline import rodar_nsga2          # já aponta para ../fase2b_benchmark
from coco_utils import rodar_no_bbob, ler_resultados_finais
from protocolo import PROTOCOLO_BBOB as P, orcamento, seed_da_instancia

OPCOES = {"20": lambda d: 20, "40": lambda d: 40, "11D-1": lambda d: 11 * d - 1}
REFERENCIA = "20"

if "--so-analise" not in sys.argv:
    for nome, regra in OPCOES.items():
        def otimizador(problema, orc, seed, regra=regra):
            rodar_nsga2(problema, tam_pop=P["tam_pop"], n_inicial=regra(problema["n_var"]),
                        orcamento=orc, seed=seed)
        print(f"Rodando amostra inicial {nome}...")
        rodar_no_bbob(otimizador, f"inicial{nome}", P["funcoes"], P["dimensoes"],
                      P["instancias"], orcamento, seed_da_instancia, progresso=False)

res = {nome: {(x["funcao"], x["dimensao"], x["instancia"]): x["delta_hv"]
              for x in ler_resultados_finais(f"exdata/inicial{nome}")} for nome in OPCOES}

linhas = ["Mediana de delta_HV final (menor é melhor), 55 funções x 15 instâncias por D",
          " D | orç. | " + " | ".join(f"{n:>21}" for n in OPCOES)]
for d in P["dimensoes"]:
    ks = [k for k in res[REFERENCIA] if k[1] == d]
    cel = [f"{np.median([res[n][k] for k in ks]):7.3f} (amostra {OPCOES[n](d):3d})" for n in OPCOES]
    linhas.append(f"{d:>2} | {orcamento(d):>4} | " + " | ".join(cel))
linhas.append("")
linhas.append(f"Wilcoxon pareado (mesma função e instância) contra amostra {REFERENCIA}: "
              "p-valor e qual é melhor")
for d in P["dimensoes"]:
    ks = [k for k in res[REFERENCIA] if k[1] == d]
    b = np.array([res[REFERENCIA][k] for k in ks])
    partes = []
    for n in OPCOES:
        if n == REFERENCIA:
            continue
        a = np.array([res[n][k] for k in ks])
        p = wilcoxon(a, b).pvalue
        melhor = n if np.median(a - b) < 0 else REFERENCIA
        partes.append(f"{n}: p = {p:.1e} (melhor: {melhor})")
    linhas.append(f"{d:>2} | " + " | ".join(partes))

print("\n".join(linhas))
os.makedirs("resultados", exist_ok=True)
with open("resultados/bbob_amostra_inicial.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")
