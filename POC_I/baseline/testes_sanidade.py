"""
testes_sanidade.py — Testes de sanidade da Fase 2 (NSGA-II baseline).

Rode com:   python3 testes_sanidade.py

Cada teste verifica uma propriedade que um NSGA-II correto PRECISA ter.
Se todos passarem, o baseline está pronto para servir de referência.
Resultados (gráficos + resumo em texto) vão para a pasta resultados/.

  T1  Convergência: com orçamento grande, a frente encontrada no ZDT1 cola
      na fronteira verdadeira (IGD pequeno, HV perto do máximo teórico).
  T2  Curva de HV: o HV cresce ao longo das avaliações.
  T3  Orçamento: o contador nunca passa do limite e bloqueia excessos.
  T4  Reprodutibilidade: mesma seed -> resultado idêntico; seed diferente
      -> resultado diferente.
  T5  Outras ZDT: o mesmo código funciona nos demais problemas.
  T1 a T5 usam a configuração do artigo original do NSGA-II (pop 100, 25.000
  avaliações), para comparar com valores conhecidos da literatura.
  T6  Baseline no protocolo PROPOSTO do POC I (protocolo.py): com poucas
      avaliações o NSGA-II fica longe da fronteira. É o problema que o
      surrogate vai atacar.
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from nsga2_baseline import rodar_nsga2, ContadorAvaliacoes, OrcamentoEsgotado
from problemas import PROBLEMAS
from metricas import hipervolume
from protocolo import PROTOCOLO_POC1, SEEDS_POC1

PASTA = "resultados"
os.makedirs(PASTA, exist_ok=True)

AZUL, LARANJA, CINZA = "#2a78d6", "#eb6834", "#8a8a8a"
plt.rcParams.update({
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": "#e6e6e6", "grid.linewidth": 0.6,
    "axes.edgecolor": "#9a9a9a", "font.size": 10,
})

linhas_relatorio = []
resultados_testes = {}


def log(msg=""):
    print(msg)
    linhas_relatorio.append(msg)


def resultado(nome, passou, detalhe):
    resultados_testes[nome] = passou
    log(f"[{'PASSOU' if passou else 'FALHOU'}] {nome}: {detalhe}")


# ---------------------------------------------------------------------------
log("=" * 70)
log("T1 — Convergência no ZDT1 com orçamento grande (25.000 avaliações)")
log("=" * 70)
r1 = rodar_nsga2("zdt1", tam_pop=100, orcamento=25000, seed=1)
final = r1["historico"][-1]
hv_max = hipervolume(PROBLEMAS["zdt1"]["fronteira"](20000))
log(f"Gerações: {final['geracao']} | HV final {final['hv']:.4f} "
    f"(máximo teórico {hv_max:.4f}, {100 * final['hv'] / hv_max:.1f}%) | "
    f"IGD final {final['igd']:.5f} | tempo {r1['tempo_s']:.1f}s")
resultado("T1 convergência",
          final["igd"] < 0.01 and final["hv"] > 0.98 * hv_max,
          "critério: IGD < 0.01 e HV > 98% do máximo teórico")

fig, ax = plt.subplots(figsize=(6, 4.5))
fv = PROBLEMAS["zdt1"]["fronteira"]()
ax.plot(fv[:, 0], fv[:, 1], color=CINZA, lw=2, label="Fronteira verdadeira")
inicial = r1["historico"][0]["frente"]
ax.scatter(inicial[:, 0], inicial[:, 1], s=22, facecolors="none",
           edgecolors=LARANJA, lw=1, label="Frente inicial (aleatória)")
ax.scatter(r1["frente_final"][:, 0], r1["frente_final"][:, 1], s=16,
           color=AZUL, label="Frente final (25.000 aval.)", zorder=3)
ax.set_xlabel("f1"); ax.set_ylabel("f2")
ax.set_title("T1 — NSGA-II no ZDT1: frente final vs. fronteira verdadeira")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{PASTA}/T1_convergencia_zdt1.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T2 — Curva de HV ao longo das avaliações")
log("=" * 70)
hv = np.array([h["hv"] for h in r1["historico"]])
av = np.array([h["avaliacoes"] for h in r1["historico"]])
quedas = np.diff(hv)
n_quedas = int((quedas < -1e-12).sum())
maior_queda = float(-quedas.min()) if quedas.min() < 0 else 0.0
log(f"HV inicial {hv[0]:.4f} -> final {hv[-1]:.4f} | "
    f"gerações com queda de HV: {n_quedas} de {len(quedas)} | maior queda: {maior_queda:.5f}")
log("Obs.: o NSGA-II é elitista, mas o HV da população pode cair um pouquinho "
    "quando o crowding descarta um ponto não dominado. Quedas devem ser raras e minúsculas.")
resultado("T2 curva de HV",
          hv[-1] > hv[0] and maior_queda < 0.01,
          "critério: HV final > inicial e nenhuma queda maior que 0.01")

fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(av, hv, color=AZUL, lw=2)
ax.axhline(hv_max, color=CINZA, lw=1, ls="--")
ax.text(av[-1], hv_max, "máximo teórico", ha="right", va="bottom", color="#555", fontsize=9)
ax.set_xlabel("Avaliações reais"); ax.set_ylabel("Hipervolume (ref = 1.1, 1.1)")
ax.set_title("T2 — Curva de convergência do NSGA-II (ZDT1)")
fig.tight_layout(); fig.savefig(f"{PASTA}/T2_curva_hv_zdt1.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T3 — Controle do orçamento")
log("=" * 70)
ok = True
for orc in (25000, 1000, 1050, 300):
    r = rodar_nsga2("zdt1", tam_pop=100 if orc >= 1000 else 20, orcamento=orc, seed=3)
    n_arquivo = len(r["arquivo_F"])
    certo = r["avaliacoes"] <= orc and n_arquivo == r["avaliacoes"]
    ok &= certo
    log(f"orçamento {orc:6d} -> avaliações usadas {r['avaliacoes']:6d} | "
        f"registros no arquivo {n_arquivo:6d} | sobra {orc - r['avaliacoes']}")
cont = ContadorAvaliacoes(PROBLEMAS["zdt1"]["funcao"], orcamento=2)
x = [0.5] * 30
cont(x); cont(x)
try:
    cont(x)
    bloqueou = False
except OrcamentoEsgotado:
    bloqueou = True
log(f"Contador com orçamento 2 bloqueou a 3ª avaliação? {bloqueou}")
resultado("T3 orçamento", ok and bloqueou,
          "critério: nunca passa do orçamento, arquivo = nº de avaliações, excesso é bloqueado")
log("Obs.: com orçamento 1050 e população 100 sobram 50 avaliações, porque o "
    "algoritmo só roda gerações completas. [EM ABERTO] se isso é aceitável ou se "
    "o orçamento deve ser sempre múltiplo da população.")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T4 — Reprodutibilidade")
log("=" * 70)
a = rodar_nsga2("zdt1", tam_pop=40, orcamento=2000, seed=7)
b = rodar_nsga2("zdt1", tam_pop=40, orcamento=2000, seed=7)
c = rodar_nsga2("zdt1", tam_pop=40, orcamento=2000, seed=8)
igual = np.array_equal(a["arquivo_F"], b["arquivo_F"])
diferente = not np.array_equal(a["arquivo_F"], c["arquivo_F"])
log(f"seed 7 vs seed 7 idênticos? {igual} | seed 7 vs seed 8 diferentes? {diferente}")
resultado("T4 reprodutibilidade", igual and diferente,
          "critério: mesma seed reproduz tudo; seed diferente muda o resultado")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T5 — Demais problemas ZDT (25.000 avaliações, pop 100, seed 1)")
log("=" * 70)
fig, axes = plt.subplots(1, 5, figsize=(17, 3.6))
for ax, nome in zip(axes, ["zdt1", "zdt2", "zdt3", "zdt4", "zdt6"]):
    r = rodar_nsga2(nome, tam_pop=100, orcamento=25000, seed=1)
    h = r["historico"][-1]
    log(f"{nome}: HV {h['hv']:.4f} | IGD {h['igd']:.5f} | pontos na frente {h['n_frente']}")
    fv = PROBLEMAS[nome]["fronteira"]()
    ax.scatter(fv[:, 0], fv[:, 1], s=1, color=CINZA)
    ax.scatter(r["frente_final"][:, 0], r["frente_final"][:, 1], s=10, color=AZUL, zorder=3)
    ax.set_title(f"{nome.upper()}  (IGD {h['igd']:.4f})")
    ax.set_xlabel("f1")
axes[0].set_ylabel("f2")
fig.suptitle("T5 — NSGA-II nas ZDT contínuas: cinza = fronteira verdadeira, azul = obtido", y=1.02)
fig.tight_layout(); fig.savefig(f"{PASTA}/T5_todas_zdt.png", dpi=150, bbox_inches="tight"); plt.close(fig)
log("Obs.: T5 não tem critério automático; é para você OLHAR os gráficos. ZDT4 é "
    "multimodal e costuma ser o mais difícil para o NSGA-II.")

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
log("T6 — Baseline no protocolo proposto do POC I (ver protocolo.py)")
log("=" * 70)
P = PROTOCOLO_POC1
log(f"{P['nome_problema'].upper()} com {P['n_var']} variáveis, orçamento {P['orcamento']}, "
    f"pop {P['tam_pop']}, ref HV {P['ref_hv']}, {len(SEEDS_POC1)} seeds. "
    "Estes são os números contra os quais a Fase 3 (surrogate) será comparada.")
fig, ax = plt.subplots(figsize=(6, 4.5))
fv = PROBLEMAS["zdt1"]["fronteira"]()
ax.plot(fv[:, 0], fv[:, 1], color=CINZA, lw=2, label="Fronteira verdadeira")
igds, hvs, hvs_curta = [], [], []
for i, seed in enumerate(SEEDS_POC1):
    r = rodar_nsga2(**P, seed=seed)
    assert r["avaliacoes"] == P["orcamento"]
    h = r["historico"][-1]
    igds.append(h["igd"]); hvs.append(h["hv"])
    hvs_curta.append(hipervolume(r["frente_final"], ref=(1.1, 1.1)))
    ax.scatter(r["frente_final"][:, 0], r["frente_final"][:, 1], s=14, color=AZUL,
               alpha=0.7, label=f"Frentes finais ({len(SEEDS_POC1)} seeds)" if i == 0 else None)
log(f"IGD final: média {np.mean(igds):.3f} ± {np.std(igds):.3f} | "
    f"HV final (ref {P['ref_hv']}): média {np.mean(hvs):.3f} ± {np.std(hvs):.3f}  "
    f"(compare com T1, 25.000 avaliações: IGD {final['igd']:.4f})")
log(f"Com a ref antiga (1.1, 1.1) o HV médio seria {np.mean(hvs_curta):.3f}: a maioria das "
    f"soluções fica fora da cerca, e por isso a referência foi ajustada ao regime de poucas avaliações.")
ax.set_xlabel("f1"); ax.set_ylabel("f2")
ax.set_title(f"T6 — Com só {P['orcamento']} avaliações, o NSGA-II fica longe da fronteira")
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(f"{PASTA}/T6_cenario_caro_zdt1.png", dpi=150); plt.close(fig)

# ---------------------------------------------------------------------------
log(""); log("=" * 70)
todos = all(resultados_testes.values())
log(f"RESUMO: {sum(resultados_testes.values())}/{len(resultados_testes)} testes automáticos passaram. "
    + ("Baseline pronto para a Fase 3." if todos else "Revisar os testes que falharam."))
with open(f"{PASTA}/relatorio_testes.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(linhas_relatorio) + "\n")
