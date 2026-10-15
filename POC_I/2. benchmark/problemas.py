"""
problemas.py — Os problemas do benchmark do projeto: a suíte bbob-biobj (COCO).

Cada problema do COCO vira um dicionário simples, para que os algoritmos
(NSGA-II, surrogate, LLM) não precisem saber de onde o problema vem:

    nome      ex.: bbob-biobj_f01_i01_d10 (função 1, instância 1, D = 10)
    funcao    recebe x (lista ou vetor com D números) e devolve (f1, f2)
    n_var     D, o número de variáveis de decisão
    limites   ([-5]*D, [5]*D): a região de busca da suíte
    coco      o objeto original do COCO

A fronteira de Pareto verdadeira é desconhecida na maioria das funções.
Por isso a qualidade é medida pelo próprio COCO (ver coco_utils.py).
"""

import numpy as np

LIMITE_BBOB = 5.0   # região de interesse da suíte: [-5, 5] em cada variável


def obter_problema_bbob(problema_coco):
    """Embrulha um problema do COCO (um item de cocoex.Suite("bbob-biobj", ...))."""
    n = problema_coco.dimension

    def funcao(individuo):
        # o COCO recebe um vetor numpy e devolve os 2 objetivos
        return tuple(problema_coco(np.asarray(individuo, dtype=float)))

    return dict(
        nome=problema_coco.id,
        funcao=funcao,
        n_var=n,
        limites=([-LIMITE_BBOB] * n, [LIMITE_BBOB] * n),
        coco=problema_coco,
    )
