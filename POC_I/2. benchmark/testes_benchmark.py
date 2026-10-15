"""
testes_benchmark.py — Confere se o benchmark está montado como o protocolo diz.

Rode com:   python3 testes_benchmark.py      (~10 s)
Saída:      resultados/relatorio_testes_benchmark.txt

  B1  A suíte tem 55 funções x 3 dimensões x 15 instâncias = 2.475 problemas,
      todos com 2 objetivos e região de busca [-5, 5].
  B2  As 55 funções formam 15 grupos de dificuldade.
  B3  Instâncias diferentes são problemas diferentes (deslocados e
      rotacionados): o mesmo x dá valores diferentes em cada instância.
  B4  O observador do COCO registra exatamente o orçamento (30 x D) e a
      execução é reprodutível (mesma seed, mesmo resultado).
"""

import os
import shutil

import cocoex
import numpy as np

from busca_aleatoria import busca_aleatoria
from coco_utils import rodar_no_bbob, ler_resultados_finais
from funcoes_bbob import tabela_funcoes
from problemas import obter_problema_bbob
from protocolo import PROTOCOLO_BBOB as P, orcamento

os.makedirs("resultados", exist_ok=True)
linhas, ok = [], {}


def resultado(nome, passou, detalhe):
    ok[nome] = passou
    msg = f"[{'PASSOU' if passou else 'FALHOU'}] {nome}: {detalhe}"
    print(msg)
    linhas.append(msg)


# B1 ------------------------------------------------------------------------
filtro = ("dimensions:" + ",".join(map(str, P["dimensoes"])) +
          f" instance_indices:{P['instancias'][0]}-{P['instancias'][-1]}")
suite = cocoex.Suite("bbob-biobj", "", filtro)
# O COCO libera cada problema quando passa para o próximo, então tudo o que
# precisamos de cada um é lido dentro do laço.
n_probs, dois_obj, limites, f_inst = 0, True, True, []
x0 = np.zeros(10)
for prob in suite:
    p = obter_problema_bbob(prob)
    n_probs += 1
    dois_obj &= prob.number_of_objectives == 2
    limites &= min(p["limites"][0]) == -5 and max(p["limites"][1]) == 5
    if prob.id_function == 1 and prob.dimension == 10:
        f_inst.append(tuple(np.round(p["funcao"](x0), 6)))   # para o teste B3
n_esperado = len(P["funcoes"]) * len(P["dimensoes"]) * len(P["instancias"])
resultado("B1 tamanho da suíte", n_probs == n_esperado and dois_obj and limites,
          f"{n_probs} problemas (esperado {n_esperado}), 2 objetivos e região [-5, 5]")

# B2 ------------------------------------------------------------------------
tab = tabela_funcoes()
n_grupos = len(set(x["grupo"] for x in tab))
resultado("B2 grupos", len(tab) == 55 and n_grupos == 15,
          f"{len(tab)} funções em {n_grupos} grupos")

# B3 ------------------------------------------------------------------------
resultado("B3 instâncias diferentes", len(set(f_inst)) == len(f_inst) == 15,
          f"f1, D = 10, x = 0: {len(set(f_inst))} valores distintos em {len(f_inst)} instâncias")

# B4 ------------------------------------------------------------------------
pastas = [rodar_no_bbob(busca_aleatoria, f"teste_benchmark_{k}", funcoes=[1, 46],
                        dimensoes=P["dimensoes"], instancias=[1, 2], orcamento=orcamento,
                        seed=lambda i: i, progresso=False) for k in (1, 2)]
r1, r2 = (sorted(ler_resultados_finais(p), key=lambda r: (r["funcao"], r["dimensao"], r["instancia"]))
          for p in pastas)
aval_ok = all(r["avaliacoes"] == orcamento(r["dimensao"]) for r in r1)
repro = [r["delta_hv"] for r in r1] == [r["delta_hv"] for r in r2]
for p in pastas:
    shutil.rmtree(p)
resultado("B4 orçamento e reprodutibilidade", aval_ok and repro,
          f"COCO registrou {sorted(set(r['avaliacoes'] for r in r1))} avaliações "
          f"(esperado 150, 300 e 600); duas rodadas idênticas? {repro}")

resumo = f"RESUMO: {sum(ok.values())}/{len(ok)} testes do benchmark passaram."
print(resumo)
linhas.append(resumo)
with open("resultados/relatorio_testes_benchmark.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")
