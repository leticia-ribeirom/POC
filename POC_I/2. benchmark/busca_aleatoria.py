"""
busca_aleatoria.py — O "piso" do benchmark: busca aleatória.

Sorteia `orcamento` soluções uniformes na região [-5, 5]^D e avalia todas.
Não aprende nada. Qualquer algoritmo que valha a pena (o NSGA-II e as
variantes com surrogate e LLM) precisa ser melhor que ela com o MESMO
orçamento; por isso ela roda junto com o baseline em
../fase2_baseline/experimento_bbob.py.
"""

import numpy as np


def busca_aleatoria(problema, orcamento, seed):
    """Mesma assinatura dos otimizadores usados em coco_utils.rodar_no_bbob."""
    rng = np.random.default_rng(seed)
    inf, sup = problema["limites"]
    for _ in range(orcamento):
        problema["funcao"](rng.uniform(inf, sup))
