"""
nsga2_baseline.py — Variante (A) do POC: NSGA-II puro, em DEAP.

Esta é a referência (baseline) contra a qual o NSGA-II + surrogate (Fase 3)
e, no POC II, o NSGA-II + surrogate + LLM serão comparados.

Pontos importantes do desenho:
  1. O algoritmo para pelo ORÇAMENTO DE AVALIAÇÕES REAIS, não pelo número
     de gerações. O orçamento é a "moeda" da comparação entre variantes.
  2. Toda chamada à função real passa por um ContadorAvaliacoes. Ele conta
     e se recusa a passar do orçamento, então é impossível "roubar".
  3. Todas as avaliações reais ficam guardadas num ARQUIVO (x, f(x)).
     No baseline o arquivo só serve para registro, mas na Fase 3 ele será
     o conjunto de treino do Random Forest.
  4. A cada geração guardamos HV, IGD e a frente atual (curva de convergência).

Parâmetros padrão: os do artigo original do NSGA-II (Deb et al., 2002):
  probabilidade de cruzamento 0.9, probabilidade de mutação por variável
  1/n, índices de distribuição eta_c = eta_m = 20.
[EM ABERTO] Tamanho da população e orçamento: decisão sua com a orientadora.
"""

import random
import time

import numpy as np
from deap import base, creator, tools

from problemas import obter_problema
from metricas import hipervolume, igd, REF_PADRAO


# ---------------------------------------------------------------------------
# 1) Tipos do DEAP: "o que é um fitness" e "o que é um indivíduo".
#    weights=(-1.0, -1.0) -> os DOIS objetivos são minimizados.
#    O if evita recriar os tipos se o módulo for importado mais de uma vez.
# ---------------------------------------------------------------------------
if not hasattr(creator, "FitnessMin2"):
    creator.create("FitnessMin2", base.Fitness, weights=(-1.0, -1.0))
if not hasattr(creator, "Individuo"):
    # Um indivíduo é uma lista de floats (as variáveis de decisão x)
    # que carrega junto um atributo .fitness com os valores (f1, f2).
    creator.create("Individuo", list, fitness=creator.FitnessMin2)


class OrcamentoEsgotado(Exception):
    """Levantada se alguém tentar avaliar além do orçamento."""


class ContadorAvaliacoes:
    """Embrulha a função-objetivo real: conta cada chamada, impõe o limite
    de orçamento e guarda (x, f(x)) no arquivo."""

    def __init__(self, funcao, orcamento):
        self.funcao = funcao
        self.orcamento = orcamento
        self.n = 0                 # avaliações reais feitas até agora
        self.arquivo_X = []        # variáveis de decisão avaliadas
        self.arquivo_F = []        # objetivos reais correspondentes

    def __call__(self, individuo):
        if self.n >= self.orcamento:
            raise OrcamentoEsgotado(
                f"Tentativa de avaliação nº {self.n + 1} com orçamento {self.orcamento}")
        self.n += 1
        valores = self.funcao(individuo)
        self.arquivo_X.append(list(individuo))
        self.arquivo_F.append(list(valores))
        return valores

    @property
    def restante(self):
        return self.orcamento - self.n


def primeira_frente(pop):
    """Devolve só os indivíduos não dominados (rank 1) da população."""
    return tools.sortNondominated(pop, len(pop), first_front_only=True)[0]


def objetivos(individuos):
    """Converte uma lista de indivíduos numa matriz (n x 2) de objetivos."""
    return np.array([ind.fitness.values for ind in individuos])


def montar_toolbox(problema, avaliar, eta_c, eta_m, prob_mut_var):
    """A 'caixa de ferramentas' do DEAP: registra cada peça do algoritmo."""
    inf, sup = problema["limites"]
    n_var = problema["n_var"]
    tb = base.Toolbox()

    # Como criar um indivíduo: cada variável sorteada uniformemente
    # dentro dos seus limites.
    def novo_vetor():
        return [random.uniform(a, b) for a, b in zip(inf, sup)]

    tb.register("individuo", tools.initIterate, creator.Individuo, novo_vetor)
    tb.register("populacao", tools.initRepeat, list, tb.individuo)

    # Avaliação: SEMPRE a função contada (nunca a função "crua").
    tb.register("evaluate", avaliar)

    # Cruzamento SBX e mutação polinomial, respeitando os limites.
    tb.register("mate", tools.cxSimulatedBinaryBounded,
                low=inf, up=sup, eta=eta_c)
    tb.register("mutate", tools.mutPolynomialBounded,
                low=inf, up=sup, eta=eta_m, indpb=prob_mut_var)

    # Seleção de sobreviventes do NSGA-II: non-dominated sorting + crowding.
    tb.register("select", tools.selNSGA2)
    return tb


def rodar_nsga2(nome_problema="zdt1", tam_pop=100, orcamento=25000, seed=1,
                prob_cx=0.9, eta_c=20.0, eta_m=20.0, prob_mut_var=None,
                ref_hv=REF_PADRAO, n_var=None, verbose=False):
    """Executa uma rodada do NSGA-II puro.

    n_var: número de variáveis de decisão (None = padrão do artigo original).

    Retorna um dicionário com:
      pop_final, frente_final (matriz de objetivos), historico (lista por
      geração), arquivo_X, arquivo_F, avaliacoes, tempo_s e a configuração.
    """
    if tam_pop % 4 != 0:
        # selTournamentDCD do DEAP exige população múltipla de 4.
        raise ValueError("tam_pop precisa ser múltiplo de 4 (exigência do selTournamentDCD).")
    if orcamento < tam_pop:
        raise ValueError("O orçamento precisa caber pelo menos a população inicial.")

    problema = obter_problema(nome_problema, n_var)
    if prob_mut_var is None:
        prob_mut_var = 1.0 / problema["n_var"]

    # Semente: mesma seed -> mesma execução (reprodutibilidade).
    random.seed(seed)
    np.random.seed(seed)

    avaliar = ContadorAvaliacoes(problema["funcao"], orcamento)
    tb = montar_toolbox(problema, avaliar, eta_c, eta_m, prob_mut_var)
    fronteira_verdadeira = problema["fronteira"]()

    historico = []

    def registrar(geracao, pop):
        frente = objetivos(primeira_frente(pop))
        historico.append(dict(
            geracao=geracao,
            avaliacoes=avaliar.n,
            hv=hipervolume(frente, ref_hv),
            igd=igd(frente, fronteira_verdadeira),
            n_frente=len(frente),
            frente=frente,
        ))
        if verbose:
            h = historico[-1]
            print(f"ger {geracao:4d} | aval {h['avaliacoes']:6d} | "
                  f"HV {h['hv']:.4f} | IGD {h['igd']:.4f} | |F1| {h['n_frente']}")

    t0 = time.perf_counter()

    # --- Passo 1: população inicial, avaliada de verdade (gasta tam_pop) ---
    pop = tb.populacao(n=tam_pop)
    for ind in pop:
        ind.fitness.values = tb.evaluate(ind)

    # Chamada "de preparação": não descarta ninguém (pede len(pop)), só
    # calcula rank e crowding distance, que o torneio abaixo precisa.
    pop = tb.select(pop, len(pop))
    registrar(0, pop)

    # --- Laço principal: só roda se couber uma geração inteira no orçamento.
    # Cada geração gasta exatamente tam_pop avaliações (uma por filho).
    # Se o orçamento não for múltiplo de tam_pop, a sobra não é usada.
    geracao = 0
    while avaliar.restante >= tam_pop:
        geracao += 1

        # Passo 2: seleção de pais por torneio binário (rank, depois crowding).
        pais = tools.selTournamentDCD(pop, len(pop))
        filhos = [tb.clone(ind) for ind in pais]

        # Passo 3: variação (cruzamento em pares + mutação em cada filho).
        for f1, f2 in zip(filhos[::2], filhos[1::2]):
            if random.random() <= prob_cx:
                tb.mate(f1, f2)
            tb.mutate(f1)
            tb.mutate(f2)
            # Os filhos mudaram: o fitness antigo (herdado do pai) não vale mais.
            del f1.fitness.values, f2.fitness.values

        # Passo 4: avaliação REAL de todos os filhos (gasta tam_pop).
        for ind in filhos:
            ind.fitness.values = tb.evaluate(ind)

        # Passo 5: sobrevivência elitista: junta pais + filhos (2N) e fica
        # com os N melhores por frentes de Pareto + crowding distance.
        pop = tb.select(pop + filhos, tam_pop)
        registrar(geracao, pop)

    tempo = time.perf_counter() - t0

    return dict(
        pop_final=pop,
        frente_final=objetivos(primeira_frente(pop)),
        historico=historico,
        arquivo_X=np.array(avaliar.arquivo_X),
        arquivo_F=np.array(avaliar.arquivo_F),
        avaliacoes=avaliar.n,
        tempo_s=tempo,
        config=dict(problema=nome_problema, n_var=problema["n_var"], tam_pop=tam_pop,
                    orcamento=orcamento, seed=seed, prob_cx=prob_cx, eta_c=eta_c,
                    eta_m=eta_m, prob_mut_var=prob_mut_var, ref_hv=ref_hv),
    )


if __name__ == "__main__":
    # Execução de demonstração com o protocolo proposto para o POC I,
    # geração a geração (verbose=True).
    from protocolo import PROTOCOLO_POC1
    r = rodar_nsga2(**PROTOCOLO_POC1, seed=1, verbose=True)
    h = r["historico"][-1]
    print(f"\nConfig: {r['config']}")
    print(f"Avaliações usadas: {r['avaliacoes']} | gerações: {h['geracao']} | "
          f"HV final: {h['hv']:.3f} | IGD final: {h['igd']:.3f} | tempo: {r['tempo_s']:.2f}s")
