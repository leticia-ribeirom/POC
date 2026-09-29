"""
problemas.py — Funções de benchmark (ZDT) e suas fronteiras de Pareto verdadeiras.

Use obter_problema(nome, n_var) para pegar a descrição de um problema:
  - funcao        : a função-objetivo "real" (do DEAP). Recebe um indivíduo
                    (lista de floats) e devolve uma tupla (f1, f2).
  - n_var         : número de variáveis de decisão (tamanho do vetor x).
  - limites       : (inferiores, superiores) de cada variável.
  - fronteira     : função que devolve pontos da fronteira de Pareto
                    verdadeira (usada no IGD e nos gráficos).

O número de variáveis padrão de cada ZDT é o do artigo original
(Zitzler, Deb & Thiele, 2000): 30 para ZDT1-3 e 10 para ZDT4 e ZDT6.
Em otimização cara é comum usar menos variáveis (por exemplo, 10), por isso
n_var pode ser ajustado. A fronteira verdadeira NÃO muda com n_var: ela é
atingida quando x2 = ... = xn estão no ótimo (g = 1).

Decisão proposta para o POC I (ver README): ZDT1 com n_var = 10.
"""

import numpy as np
from deap import benchmarks


def _pareto_nao_dominado(F):
    """Remove pontos dominados de um conjunto (minimização).
    Usado só para montar a fronteira do ZDT3, que é desconexa."""
    F = np.asarray(F)
    manter = np.ones(len(F), dtype=bool)
    for i in range(len(F)):
        if not manter[i]:
            continue
        domina_i = np.all(F <= F[i], axis=1) & np.any(F < F[i], axis=1)
        if domina_i.any():
            manter[i] = False
    return F[manter]


def fronteira_zdt1(n_pontos=1000):
    f1 = np.linspace(0, 1, n_pontos)
    return np.column_stack([f1, 1 - np.sqrt(f1)])


def fronteira_zdt2(n_pontos=1000):
    f1 = np.linspace(0, 1, n_pontos)
    return np.column_stack([f1, 1 - f1 ** 2])


def fronteira_zdt3(n_pontos=10000):
    f1 = np.linspace(0, 1, n_pontos)
    f2 = 1 - np.sqrt(f1) - f1 * np.sin(10 * np.pi * f1)
    return _pareto_nao_dominado(np.column_stack([f1, f2]))


def fronteira_zdt6(n_pontos=1000):
    # No ZDT6 a fronteira começa em f1 ≈ 0.2808 (não em 0).
    f1 = np.linspace(0.280775319, 1, n_pontos)
    return np.column_stack([f1, 1 - f1 ** 2])


# (função, n_var padrão, limite de x1, limite das demais variáveis, fronteira)
_DEFINICOES = {
    "zdt1": (benchmarks.zdt1, 30, (0.0, 1.0), (0.0, 1.0), fronteira_zdt1),
    "zdt2": (benchmarks.zdt2, 30, (0.0, 1.0), (0.0, 1.0), fronteira_zdt2),
    "zdt3": (benchmarks.zdt3, 30, (0.0, 1.0), (0.0, 1.0), fronteira_zdt3),
    # ZDT4: x1 em [0,1], demais em [-5,5] (é o que cria as "armadilhas").
    "zdt4": (benchmarks.zdt4, 10, (0.0, 1.0), (-5.0, 5.0), fronteira_zdt1),
    "zdt6": (benchmarks.zdt6, 10, (0.0, 1.0), (0.0, 1.0), fronteira_zdt6),
}


def obter_problema(nome, n_var=None):
    funcao, n_padrao, lim_x1, lim_resto, fronteira = _DEFINICOES[nome]
    n = n_padrao if n_var is None else n_var
    if n < 2:
        raise ValueError("ZDT precisa de pelo menos 2 variáveis.")
    inf = [lim_x1[0]] + [lim_resto[0]] * (n - 1)
    sup = [lim_x1[1]] + [lim_resto[1]] * (n - 1)
    return dict(nome=nome, funcao=funcao, n_var=n, limites=(inf, sup),
                fronteira=fronteira)


# Mantido por compatibilidade: problemas com o n_var padrão do artigo original.
PROBLEMAS = {nome: obter_problema(nome) for nome in _DEFINICOES}
