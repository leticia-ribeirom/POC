"""
metricas.py — Hipervolume (HV) e IGD.

Lembrete:
  - HV : área dominada até um ponto de referência. MAIOR é melhor.
  - IGD: distância média de cada ponto da fronteira verdadeira até a
         solução obtida mais próxima. MENOR é melhor.

[EM ABERTO] O ponto de referência do HV é decisão experimental. Aqui uso,
como padrão, (1.1, 1.1): o pior valor de cada objetivo na fronteira
verdadeira do ZDT1/2/3/4/6 (que é 1) mais 10%. É uma convenção comum, mas
precisa ser combinada com a orientadora e mantida IGUAL em todas as
variantes (A, B e C). Pontos piores que a referência não contam no HV.
"""

import numpy as np
import moocore
from scipy.spatial.distance import cdist

REF_PADRAO = (1.1, 1.1)


def hipervolume(F, ref=REF_PADRAO):
    """F: matriz (n_solucoes x n_objetivos) com valores REAIS dos objetivos."""
    F = np.asarray(F, dtype=float)
    if len(F) == 0:
        return 0.0
    return float(moocore.hypervolume(F, ref=np.asarray(ref, dtype=float)))


def igd(F, fronteira_verdadeira):
    """Para cada ponto da fronteira verdadeira, pega a distância até a
    solução obtida mais próxima, e tira a média."""
    F = np.asarray(F, dtype=float)
    distancias = cdist(fronteira_verdadeira, F)   # linhas = fronteira verdadeira
    return float(np.mean(np.min(distancias, axis=1)))
