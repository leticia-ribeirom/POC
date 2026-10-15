"""
testes_baseline.py — Testes de correção do NSGA-II, feitos no próprio bbob-biobj.

Rode com:   python3 testes_baseline.py      (~1 min)
Saídas:     resultados/relatorio_testes.txt e resultados/T1_convergencia_orcamento_grande.png

Cada teste verifica uma propriedade que um NSGA-II correto PRECISA ter.

  T1  Convergência: com orçamento grande (20.000 avaliações), o NSGA-II chega
      muito perto da referência do COCO nas funções mais fáceis da suíte
      (f1, f2 e f11 em D = 5), e o resultado melhora quando o orçamento cresce.
      Como a fronteira verdadeira do bbob-biobj não é conhecida, é a
      referência do COCO (a melhor aproximação conhecida) que faz esse papel.
  T2  Orçamento: usa exatamente 30 x D avaliações (150, 300, 600), inclusive
      com a geração final parcial em D = 5, e bloqueia qualquer excesso.
  T3  Reprodutibilidade: mesma seed -> resultado idêntico; seed diferente ->
      resultado diferente.
  T4  Amostra inicial (n_inicial): igual à população não muda nada; maior que
      a população respeita o orçamento.
  T5  COCO: o observador do COCO conta exatamente as mesmas avaliações que o
      contador do NSGA-II.
  T6  Melhor que o acaso: em D = 10, instância 1, o NSGA-II termina com
      delta_HV menor que a busca aleatória na grande maioria das 55 funções.
"""

import os
import shutil

import cocoex
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nsga2_baseline import rodar_nsga2, ContadorAvaliacoes, OrcamentoEsgotado  # também acha a pasta do benchmark
from busca_aleatoria import busca_aleatoria
from coco_utils import rodar_no_bbob, ler_resultados_finais
from grafico_convergencia import trajetorias
from problemas import obter_problema_bbob
from protocolo import PROTOCOLO_BBOB as P, orcamento

PASTA = "resultados"
os.makedirs(PASTA, exist_ok=True)
linhas, ok = [], {}
_suites = []   # mantém as suítes vivas (o COCO libera o problema junto com a suíte)


def log(msg=""):
    print(msg)
    linhas.append(msg)


def resultado(nome, passou, detalhe):
    ok[nome] = passou
    log(f"[{'PASSOU' if passou else 'FALHOU'}] {nome}: {detalhe}")


def problema(funcao, dim, inst=1):
    """Um problema do bbob-biobj SEM observador (para testes rápidos)."""
    suite = cocoex.Suite("bbob-biobj", "", "")
    _suites.append(suite)
    return obter_problema_bbob(
        suite.get_problem_by_function_dimension_instance(funcao, dim, inst))


# ---------------------------------------------------------------------------
log("=" * 70)
log("T1 — Convergência com orçamento grande (f1, f2, f11; D = 5; população 100)")
log("=" * 70)
ORCS = (300, 3000, 20000)
FUNCS = (1, 2, 11)
finais = {}
for orc in ORCS:
    pasta = rodar_no_bbob(
        lambda pr, o, s: rodar_nsga2(problema=pr, tam_pop=100, orcamento=o, seed=s),
        f"teste_T1_{orc}", funcoes=list(FUNCS), dimensoes=[5], instancias=[1],
        orcamento=lambda d, orc=orc: orc, seed=lambda i: i, progresso=False)
    for r in ler_resultados_finais(pasta):
        finais[(r["funcao"], orc)] = r["delta_hv"]
    if orc == ORCS[-1]:
        trajs = [trajetorias(pasta, 5, funcao=f)[0] for f in FUNCS]
    else:
        shutil.rmtree(pasta)
for f in FUNCS:
    log(f"f{f}: delta_HV " + " -> ".join(f"{finais[(f, o)]:.5f} ({o} aval.)" for o in ORCS))
melhora = all(finais[(f, ORCS[0])] > finais[(f, ORCS[1])] > finais[(f, ORCS[2])] for f in FUNCS)
perto = all(finais[(f, ORCS[-1])] < 0.005 for f in FUNCS)
resultado("T1 convergência", melhora and perto,
          "critério: delta_HV cai quando o orçamento cresce e fica < 0.005 com 20.000 avaliações")

fig, ax = plt.subplots(figsize=(6.4, 4))
for f, t, cor in zip(FUNCS, trajs, ("#2a78d6", "#eb6834", "#1baf7a")):
    a, v = np.array(t).T
    ax.step(a, v, where="post", color=cor, lw=2)
    ax.text(a[-1] * 1.15, v[-1] * {1: 1.0, 2: 1.25, 11: 0.8}[f], f"f{f}", va="center",
            color=cor, fontsize=9)
ax.axvline(orcamento(5), color="#8a8a8a", lw=1, ls="--")
ax.text(orcamento(5) * 1.1, 0.5, "orçamento do\nprojeto (150)", color="#555", fontsize=9)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("avaliações reais"); ax.set_ylabel("delta_HV do COCO (menor é melhor)")
ax.set_title("T1 — Com orçamento grande, o NSGA-II chega perto da referência", fontsize=11)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(f"{PASTA}/T1_convergencia_orcamento_grande.png", dpi=150)
plt.close(fig)
shutil.rmtree(f"exdata/teste_T1_{ORCS[-1]}")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T2 — Controle do orçamento (30 x D)")
log("=" * 70)
certo = True
for d in P["dimensoes"]:
    r = rodar_nsga2(problema(1, d), tam_pop=P["tam_pop"], orcamento=orcamento(d), seed=3)
    filhos_ultima = r["historico"][-1]["avaliacoes"] - r["historico"][-2]["avaliacoes"]
    c = r["avaliacoes"] == orcamento(d) and len(r["arquivo_F"]) == orcamento(d)
    certo &= c
    log(f"D = {d:2d}: orçamento {orcamento(d)} -> avaliações {r['avaliacoes']}, arquivo "
        f"{len(r['arquivo_F'])}, gerações {r['historico'][-1]['geracao']}, "
        f"filhos avaliados na última geração {filhos_ultima}")
cont = ContadorAvaliacoes(problema(1, 5)["funcao"], orcamento=2)
x = [0.0] * 5
cont(x); cont(x)
try:
    cont(x)
    bloqueou = False
except OrcamentoEsgotado:
    bloqueou = True
log(f"Contador com orçamento 2 bloqueou a 3ª avaliação? {bloqueou}")
resultado("T2 orçamento", certo and bloqueou,
          "critério: usa exatamente 30 x D, arquivo = nº de avaliações, excesso é bloqueado")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T3 — Reprodutibilidade")
log("=" * 70)
pr = problema(20, 10)
a = rodar_nsga2(pr, orcamento=300, seed=7)
b = rodar_nsga2(pr, orcamento=300, seed=7)
c = rodar_nsga2(pr, orcamento=300, seed=8)
igual = np.array_equal(a["arquivo_F"], b["arquivo_F"])
diferente = not np.array_equal(a["arquivo_F"], c["arquivo_F"])
log(f"seed 7 x seed 7 idênticos? {igual} | seed 7 x seed 8 diferentes? {diferente}")
resultado("T3 reprodutibilidade", igual and diferente,
          "critério: mesma seed reproduz tudo; seed diferente muda o resultado")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T4 — Amostra inicial (n_inicial)")
log("=" * 70)
pr = problema(20, 10)
sem = rodar_nsga2(pr, tam_pop=20, orcamento=300, seed=5)
com = rodar_nsga2(pr, tam_pop=20, orcamento=300, seed=5, n_inicial=20)
identico = np.array_equal(sem["arquivo_F"], com["arquivo_F"])
g = rodar_nsga2(pr, tam_pop=20, orcamento=300, seed=5, n_inicial=100)
conta_ok = (g["avaliacoes"] == 300 and g["historico"][0]["avaliacoes"] == 100
            and g["historico"][-1]["geracao"] == 10 and len(g["pop_final"]) == 20)
log(f"n_inicial = 20 idêntico ao clássico? {identico} | n_inicial = 100: avaliações "
    f"{g['avaliacoes']}, após a amostra {g['historico'][0]['avaliacoes']}, "
    f"gerações {g['historico'][-1]['geracao']}, população final {len(g['pop_final'])}")
resultado("T4 amostra inicial", identico and conta_ok,
          "critério: n_inicial = população não muda nada; n_inicial maior respeita o orçamento")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T5 — O COCO conta as mesmas avaliações que o NSGA-II")
log("=" * 70)
contagens = {}


def _nsga2_coco(problema_, orc, seed):
    r = rodar_nsga2(problema_, tam_pop=P["tam_pop"], orcamento=orc, seed=seed)
    contagens[(problema_["coco"].id_function, problema_["n_var"])] = r["avaliacoes"]


pasta = rodar_no_bbob(_nsga2_coco, "teste_T5", funcoes=[1, 46], dimensoes=P["dimensoes"],
                      instancias=[1], orcamento=orcamento, seed=lambda i: i, progresso=False)
coco = {(r["funcao"], r["dimensao"]): r["avaliacoes"] for r in ler_resultados_finais(pasta)}
shutil.rmtree(pasta)
log(f"NSGA-II: {sorted(contagens.items())}")
log(f"COCO:    {sorted(coco.items())}")
resultado("T5 integração COCO", coco == contagens and
          all(v == orcamento(k[1]) for k, v in coco.items()),
          "critério: as duas contagens batem e são iguais a 30 x D")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T6 — Melhor que a busca aleatória (55 funções, D = 10, instância 1)")
log("=" * 70)
cfg = dict(funcoes=P["funcoes"], dimensoes=[10], instancias=[1], orcamento=orcamento,
           seed=lambda i: i, progresso=False)
pa = rodar_no_bbob(lambda pr_, o, s: rodar_nsga2(pr_, tam_pop=P["tam_pop"], orcamento=o, seed=s),
                   "teste_T6_nsga2", **cfg)
pb = rodar_no_bbob(busca_aleatoria, "teste_T6_aleatoria", **cfg)
ra = {r["funcao"]: r["delta_hv"] for r in ler_resultados_finais(pa)}
rb = {r["funcao"]: r["delta_hv"] for r in ler_resultados_finais(pb)}
shutil.rmtree(pa); shutil.rmtree(pb)
frac = np.mean([ra[f] < rb[f] for f in ra])
log(f"NSGA-II melhor em {100 * frac:.0f}% das 55 funções | mediana {np.median(list(ra.values())):.3f} "
    f"x aleatória {np.median(list(rb.values())):.3f}")
resultado("T6 melhor que o acaso", frac >= 0.8,
          "critério: NSGA-II com delta_HV menor que a aleatória em pelo menos 80% das funções")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
todos = all(ok.values())
log(f"RESUMO: {sum(ok.values())}/{len(ok)} testes automáticos passaram. "
    + ("Baseline pronto para a Fase 3." if todos else "Revisar os testes que falharam."))
with open(f"{PASTA}/relatorio_testes.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas) + "\n")
if os.path.isdir("exdata") and not os.listdir("exdata"):
    os.rmdir("exdata")
