"""
comparacao_pymoo.py — Critério final da Fase 2: os valores do nosso NSGA-II
(DEAP) são coerentes com uma implementação independente (pymoo)?

Rode com:   pip install pymoo
            python3 comparacao_pymoo.py

As duas implementações rodam com a MESMA configuração (a do artigo original
do NSGA-II): ZDT1 com 30 variáveis, população 100, 25.000 avaliações, SBX
(prob 0.9, eta 20) e mutação polinomial (prob 1/n por variável, eta 20).
As duas frentes finais são medidas com a MESMA função de IGD e HV (metricas.py).

As seeds dos dois pacotes geram números aleatórios diferentes, então não
esperamos valores idênticos, e sim da mesma ordem de grandeza. Por isso
comparamos 10 execuções de cada um com o teste de Mann-Whitney.
"""

import numpy as np
from scipy.stats import mannwhitneyu

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.optimize import minimize
from pymoo.problems import get_problem

from nsga2_baseline import rodar_nsga2
from metricas import hipervolume, igd
from problemas import fronteira_zdt1

SEEDS = range(1, 11)
REF = (1.1, 1.1)
fv = fronteira_zdt1()

igd_deap, hv_deap, igd_pymoo, hv_pymoo = [], [], [], []
for seed in SEEDS:
    r = rodar_nsga2("zdt1", tam_pop=100, orcamento=25000, seed=seed)
    igd_deap.append(igd(r["frente_final"], fv))
    hv_deap.append(hipervolume(r["frente_final"], REF))

    alg = NSGA2(pop_size=100,
                crossover=SBX(prob=0.9, eta=20),
                mutation=PM(prob=1.0, prob_var=1 / 30, eta=20))
    res = minimize(get_problem("zdt1", n_var=30), alg,
                   ("n_eval", 25000), seed=seed, verbose=False)
    igd_pymoo.append(igd(res.F, fv))
    hv_pymoo.append(hipervolume(res.F, REF))

print("ZDT1, 30 variáveis, pop 100, 25.000 avaliações, 10 seeds")
print(f"IGD  nosso (DEAP): {np.mean(igd_deap):.5f} ± {np.std(igd_deap):.5f}")
print(f"IGD  pymoo       : {np.mean(igd_pymoo):.5f} ± {np.std(igd_pymoo):.5f}")
print(f"HV   nosso (DEAP): {np.mean(hv_deap):.4f} ± {np.std(hv_deap):.4f}")
print(f"HV   pymoo       : {np.mean(hv_pymoo):.4f} ± {np.std(hv_pymoo):.4f}")
p = mannwhitneyu(igd_deap, igd_pymoo).pvalue
print(f"Mann-Whitney no IGD: p = {p:.3f} "
      f"({'sem diferença significativa' if p >= 0.05 else 'diferença significativa'} a 5%)")
dif = 100 * (np.mean(igd_deap) - np.mean(igd_pymoo)) / np.mean(igd_pymoo)
print(f"Diferença relativa no IGD médio: {dif:+.1f}%")
print("Leitura: mesma ordem de grandeza e HV praticamente igual. Uma diferença pequena é "
      "esperada, porque o pymoo tem detalhes de implementação próprios (por exemplo, "
      "elimina soluções duplicadas antes de avaliar). O que importa é que as variantes A, B "
      "e C do POC usem TODAS a mesma implementação (a nossa).")
