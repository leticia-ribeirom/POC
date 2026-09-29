"""
metricas.py — Hipervolume (HV) e IGD.

Lembrete:
  - HV : área dominada até um ponto de referência. MAIOR é melhor.
  - IGD: distância média de cada ponto da fronteira verdadeira até a
         solução obtida mais próxima. MENOR é melhor.
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
