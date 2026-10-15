"""
protocolo.py — Protocolo experimental do projeto (decidido em 13/10/2026,
na reunião com a orientadora).

Todas as variantes (A: NSGA-II, B: NSGA-II + surrogate, C: NSGA-II +
surrogate + LLM) usam exatamente estes valores, para a comparação ser justa.
Ver README desta pasta (benchmark) e de ../1. baseline (algoritmo).
"""

# ---------------------------------------------------------------------------
# Benchmark e cenário experimental
# ---------------------------------------------------------------------------
PROTOCOLO_BBOB = dict(
    suite="bbob-biobj",              # 55 funções de 2 objetivos (COCO)
    funcoes=list(range(1, 56)),      # todas as 55
    dimensoes=[5, 10, 20],           # número de variáveis de decisão
    instancias=list(range(1, 16)),   # 15 instâncias = 15 repetições
    orcamento_por_dimensao=30,       # orçamento = 30 x D avaliações reais
                                     # (D=5: 150, D=10: 300, D=20: 600)
                                     # [PROPOSTA] a confirmar com a orientadora
    # Configuração comum às três variantes (decidida no bbob-biobj,
    # ../1. baseline/experimento_populacao.py e experimento_amostra_inicial.py)
    tam_pop=20,                      # soluções mantidas por geração
    n_inicial=20,                    # amostra inicial [EM ABERTO para a Fase 3]
)


def orcamento(dimensao):
    """Número de avaliações reais permitidas para uma dimensão."""
    return PROTOCOLO_BBOB["orcamento_por_dimensao"] * dimensao


def seed_da_instancia(instancia):
    """Uma execução por instância. A seed do algoritmo é o próprio número da
    instância, igual para todas as variantes e funções. Assim, a variante A e
    a variante B partem da mesma amostra inicial em cada instância."""
    return instancia


# ---------------------------------------------------------------------------
# Variante B (surrogate): candidatos gerados por geração, ANTES do filtro do
# Random Forest. Só tam_pop (20) são avaliados de verdade, então o orçamento por
# geração não muda. Decidido em 13/10/2026: ampliar a exploração por aqui (e
# não pela população). Os três valores serão comparados na Fase 3.
# ---------------------------------------------------------------------------
N_CANDIDATOS_OPCOES = [100, 200, 500]
N_CANDIDATOS_FASE3 = 100   # provisório; definido pelo experimento da Fase 3

# ---------------------------------------------------------------------------
# Variante C (LLM): modelo acessado por API paga. Decidido em 13/10/2026:
# API do Claude (Anthropic). Modelo exato, prompt, frequência das chamadas e
# se o LLM soma ou substitui candidatos: [EM ABERTO].
# ---------------------------------------------------------------------------
LLM_PROVEDOR = "Anthropic (API do Claude)"
