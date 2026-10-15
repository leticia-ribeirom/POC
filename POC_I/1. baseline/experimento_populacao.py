"""
experimento_populacao.py — Qual tamanho de população usar no bbob-biobj?

Rode com:   python3 experimento_populacao.py          (~10 min)
            python3 experimento_populacao.py --so-analise
            (só refaz a tabela a partir dos dados já em exdata/)

Testa as populações 8, 12, 20, 40, 60 e 100 no protocolo do projeto: 55
funções x D = 5, 10, 20 x instâncias 1 a 15, orçamento 30 x D. Em cada caso a
amostra inicial tem o mesmo tamanho da população.

Saída: resultados/bbob_populacao.txt
"""

import os
import sys

import numpy as np
from scipy.stats import wilcoxon

from nsga2_baseline import rodar_nsga2          # já aponta para ../fase2b_benchmark
from coco_utils import rodar_no_bbob, ler_resultados_finais
from protocolo import PROTOCOLO_BBOB as P, orcamento, seed_da_instancia

POPULACOES = (8, 12, 20, 40, 60, 100)   # múltiplos de 4 (exigência do DEAP)
REFERENCIA = 20

if "--so-analise" not in sys.argv:
    for N in POPULACOES:
        def otimizador(problema, orc, seed, N=N):
            rodar_nsga2(problema=problema, tam_pop=N, n_inicial=N, orcamento=orc,
                        seed=seed)
        print(f"Rodando população {N}...")
        rodar_no_bbob(otimizador, f"pop{N}", P["funcoes"], P["dimensoes"],
                      P["instancias"], orcamento, seed_da_instancia, progresso=False)

res = {N: {(x["funcao"], x["dimensao"], x["instancia"]): x["delta_hv"]
           for x in ler_resultados_finais(f"exdata/pop{N}")} for N in POPULACOES}

linhas = []
linhas.append("Mediana de delta_HV final (menor é melhor), 55 funções x 15 instâncias por D")
linhas.append(" D | orç. | " + " | ".join(f"pop {N:>3}" for N in POPULACOES))
for d in P["dimensoes"]:
    ks = [k for k in res[REFERENCIA] if k[1] == d]
    linhas.append(f"{d:>2} | {orcamento(d):>4} | " +
                  " | ".join(f"{np.median([res[N][k] for k in ks]):7.3f}" for N in POPULACOES))
linhas.append("")
linhas.append(f"Wilcoxon pareado (mesma função e instância) contra pop {REFERENCIA}: "
              "p-valor e qual população é melhor")
for d in P["dimensoes"]:
    ks = [k for k in res[REFERENCIA] if k[1] == d]
    b = np.array([res[REFERENCIA][k] for k in ks])
    partes = []
    for N in POPULACOES:
        if N == REFERENCIA:
            partes.append("      —      ")
            continue
        a = np.array([res[N][k] for k in ks])
        p = wilcoxon(a, b).pvalue
        melhor = N if np.median(a - b) < 0 else REFERENCIA
        partes.append(f"{p:7.1e} pop{melhor:<3}")
    linhas.append(f"{d:>2} | " + " | ".join(partes))

print("\n".join(linhas))
with open("resultados/bbob_populacao.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")
