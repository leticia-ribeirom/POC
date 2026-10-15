"""
caminho_benchmark.py — Encontra a pasta do benchmark e a deixa disponível
para os imports (protocolo, problemas, coco_utils, busca_aleatoria, funcoes_bbob).

A pasta do benchmark fica AO LADO desta pasta. Ela é encontrada pelo conteúdo
(é a pasta vizinha que tem coco_utils.py e protocolo.py), e não pelo nome,
então você pode renomear as pastas como quiser (ex.: "1. baseline" e
"2. benchmark").
"""

import os
import sys

_AQUI = os.path.dirname(os.path.abspath(__file__))
_PAI = os.path.dirname(_AQUI)


def achar_pasta_benchmark():
    for nome in sorted(os.listdir(_PAI)):
        pasta = os.path.join(_PAI, nome)
        if (pasta != _AQUI and os.path.isfile(os.path.join(pasta, "coco_utils.py"))
                and os.path.isfile(os.path.join(pasta, "protocolo.py"))):
            return pasta
    raise FileNotFoundError(
        "Não achei a pasta do benchmark (a que tem coco_utils.py e protocolo.py). "
        f"Ela precisa ficar ao lado desta pasta, dentro de {_PAI}")


PASTA_BENCHMARK = achar_pasta_benchmark()
if PASTA_BENCHMARK not in sys.path:
    sys.path.insert(0, PASTA_BENCHMARK)
