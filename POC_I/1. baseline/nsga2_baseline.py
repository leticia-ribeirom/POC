"""
nsga2_baseline.py — Variante A do projeto: NSGA-II puro, em DEAP, no bbob-biobj.

Esta é a referência (baseline) contra a qual o NSGA-II + surrogate (variante B)
e o NSGA-II + surrogate + LLM (variante C) serão comparados.

Pontos importantes do desenho:
  1. O algoritmo para pelo ORÇAMENTO DE AVALIAÇÕES REAIS (30 x D), não pelo
     número de gerações. O orçamento é a "moeda" da comparação entre variantes.
  2. Toda chamada à função real passa por um ContadorAvaliacoes. Ele conta
     e se recusa a passar do orçamento, então é impossível "roubar".
  3. Todas as avaliações reais ficam guardadas num ARQUIVO (x, f(x)).
     No baseline o arquivo só serve para registro, mas na Fase 3 ele será
     o conjunto de treino do Random Forest.
  4. A qualidade NÃO é calculada aqui: o observador do COCO registra cada
     avaliação e calcula o indicador oficial (ver ../fase2b_benchmark).

Operadores e parâmetros: os do artigo original do NSGA-II (DEB et al., 2002):
  cruzamento SBX (probabilidade 0.9, eta_c = 20), mutação polinomial
  (probabilidade 1/D por variável, eta_m = 20).
População e amostra inicial: protocolo.py (decididas no próprio bbob-biobj).
"""

import random
import time

import numpy as np
from deap import base, creator, tools

import os
import sys

# O benchmark (problemas, protocolo, COCO) fica na pasta ../fase2b_benchmark.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "fase2b_benchmark"))


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


def rodar_nsga2(problema, tam_pop=20, orcamento=300, seed=1,
                prob_cx=0.9, eta_c=20.0, eta_m=20.0, prob_mut_var=None,
                n_inicial=None, verbose=False):
    """Executa uma rodada do NSGA-II puro.

    problema: um dicionário de problemas.obter_problema_bbob (função, D, limites).
    n_inicial: tamanho da AMOSTRA INICIAL, isto é, quantas soluções aleatórias
      são avaliadas antes de a evolução começar. None = igual a tam_pop, que é o
      NSGA-II clássico. Se for maior que tam_pop, avaliamos n_inicial soluções e
      a população que começa a evoluir são as tam_pop melhores delas (por frente
      de Pareto + crowding). Na Fase 3, essa amostra inicial é o primeiro
      conjunto de treino do Random Forest. [EM ABERTO] qual valor usar.

    Retorna um dicionário com:
      pop_final, frente_final (matriz de objetivos), historico (lista por
      geração), arquivo_X, arquivo_F, avaliacoes, tempo_s e a configuração.
    """
    if tam_pop % 4 != 0:
        # selTournamentDCD do DEAP exige população múltipla de 4.
        raise ValueError("tam_pop precisa ser múltiplo de 4 (exigência do selTournamentDCD).")
    if n_inicial is None:
        n_inicial = tam_pop          # NSGA-II clássico: amostra inicial = população
    if n_inicial < tam_pop:
        raise ValueError("n_inicial não pode ser menor que tam_pop.")
    if orcamento < n_inicial:
        raise ValueError("O orçamento precisa caber pelo menos a amostra inicial.")

    if prob_mut_var is None:
        prob_mut_var = 1.0 / problema["n_var"]

    # Semente: mesma seed -> mesma execução (reprodutibilidade).
    random.seed(seed)
    np.random.seed(seed)

    avaliar = ContadorAvaliacoes(problema["funcao"], orcamento)
    tb = montar_toolbox(problema, avaliar, eta_c, eta_m, prob_mut_var)

    historico = []

    def registrar(geracao, pop):
        frente = objetivos(primeira_frente(pop))
        historico.append(dict(
            geracao=geracao,
            avaliacoes=avaliar.n,
            n_frente=len(frente),
            frente=frente,
        ))
        if verbose:
            h = historico[-1]
            print(f"ger {geracao:4d} | aval {h['avaliacoes']:6d} | "
                  f"soluções não dominadas na população: {h['n_frente']}")

    t0 = time.perf_counter()

    # --- Passo 1: amostra inicial, avaliada de verdade (gasta n_inicial) ---
    amostra = tb.populacao(n=n_inicial)
    for ind in amostra:
        ind.fitness.values = tb.evaluate(ind)

    # Fica com as tam_pop melhores da amostra (frente de Pareto + crowding).
    # Se n_inicial == tam_pop (o caso clássico), ninguém é descartado: a chamada
    # só calcula rank e crowding distance, que o torneio abaixo precisa.
    pop = tb.select(amostra, tam_pop)
    registrar(0, pop)

    # --- Laço principal: roda enquanto houver orçamento.
    # Cada geração gasta tam_pop avaliações (uma por filho). Se, no fim, sobrar
    # menos que tam_pop, a ÚLTIMA geração avalia só os filhos que cabem no
    # orçamento (os demais são descartados sem avaliar). Assim o orçamento é
    # usado por inteiro mesmo quando não é múltiplo de tam_pop (ex.: 150
    # avaliações com população 20, em D = 5). Quando é múltiplo, nada muda.
    geracao = 0
    while avaliar.restante > 0:
        geracao += 1
        n_avaliar = min(tam_pop, avaliar.restante)

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

        # Passo 4: avaliação REAL dos filhos (gasta tam_pop, ou o que restar).
        filhos = filhos[:n_avaliar]
        for ind in filhos:
            ind.fitness.values = tb.evaluate(ind)

        # Passo 5: sobrevivência elitista: junta pais + filhos (2N) e fica
        # com os N melhores por frentes de Pareto + crowding distance.
        # (Na última geração parcial, junta pais + os filhos que foram avaliados.)
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
        config=dict(problema=problema["nome"], n_var=problema["n_var"], tam_pop=tam_pop,
                    n_inicial=n_inicial, orcamento=orcamento, seed=seed, prob_cx=prob_cx, eta_c=eta_c,
                    eta_m=eta_m, prob_mut_var=prob_mut_var),
    )


if __name__ == "__main__":
    # Demonstração: uma execução no benchmark do projeto (bbob-biobj),
    # função 1, dimensão 10, instância 1, com o observador do COCO ligado.
    from coco_utils import rodar_no_bbob, ler_resultados_finais
    from protocolo import PROTOCOLO_BBOB as P, orcamento, seed_da_instancia

    ultimo = {}

    def otimizador(problema, orc, seed):
        ultimo["r"] = rodar_nsga2(problema=problema, tam_pop=P["tam_pop"],
                                  n_inicial=P["n_inicial"], orcamento=orc,
                                  seed=seed, verbose=True)

    pasta = rodar_no_bbob(otimizador, "demo", funcoes=[1], dimensoes=[10],
                          instancias=[1], orcamento=orcamento,
                          seed=seed_da_instancia, progresso=False)
    r = ultimo["r"]
    final = ler_resultados_finais(pasta)[0]
    print(f"\nProblema: {r['config']['problema']} | avaliações: {r['avaliacoes']} | "
          f"gerações: {r['historico'][-1]['geracao']} | "
          f"delta_HV final (COCO, menor é melhor): {final['delta_hv']:.3f} | "
          f"tempo: {r['tempo_s']:.2f}s")
