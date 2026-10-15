"""
funcoes_bbob.py — As 55 funções do bbob-biobj: de que são feitas e a que grupo
de dificuldade pertencem.

Rode com:   python3 funcoes_bbob.py
Saída:      resultados/funcoes_bbob_biobj.csv (e a tabela na tela)

Cada função do bbob-biobj junta DUAS funções da suíte bbob (de um objetivo),
escolhidas entre 10. Cada uma dessas 10 pertence a uma classe de dificuldade;
o par de classes define o grupo da função bi-objetivo (15 grupos)
(TUŠAR et al., 2016; BROCKHOFF et al., 2022).
"""

import csv
import os
import re

import cocoex

NOME_BBOB = {1: "Sphere", 2: "Elipsoide separável", 6: "Setor atrativo",
             8: "Rosenbrock", 13: "Crista afiada", 14: "Soma de potências",
             15: "Rastrigin", 17: "Schaffer F7", 20: "Schwefel", 21: "Gallagher 101"}
CLASSE = {1: "separável", 2: "separável", 6: "moderada", 8: "moderada",
          13: "mal-condicionada", 14: "mal-condicionada", 15: "multimodal",
          17: "multimodal", 20: "fracamente estruturada", 21: "fracamente estruturada"}


def tabela_funcoes():
    """Lista de dicionários: funcao, f_bbob_1, f_bbob_2, nomes e grupo."""
    linhas = []
    for prob in cocoex.Suite("bbob-biobj", "", "dimensions:5 instance_indices:1"):
        a, b = [int(x) for x in re.findall(r"bbob_f(\d+)", prob.name)]
        linhas.append(dict(funcao=prob.id_function, f_bbob_1=a, f_bbob_2=b,
                           objetivo_1=NOME_BBOB[a], objetivo_2=NOME_BBOB[b],
                           grupo=f"{CLASSE[a]} + {CLASSE[b]}"))
    return linhas


def grupo_da_funcao():
    """{número da função bi-objetivo: nome do grupo}."""
    return {x["funcao"]: x["grupo"] for x in tabela_funcoes()}


if __name__ == "__main__":
    os.makedirs("resultados", exist_ok=True)
    tab = tabela_funcoes()
    with open("resultados/funcoes_bbob_biobj.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(tab[0]))
        w.writeheader()
        w.writerows(tab)
    for x in tab:
        print(f"f{x['funcao']:02d}  {x['objetivo_1']:<20} x {x['objetivo_2']:<20} {x['grupo']}")
    print(f"\n{len(tab)} funções, {len(set(x['grupo'] for x in tab))} grupos. "
          "Tabela salva em resultados/funcoes_bbob_biobj.csv")
