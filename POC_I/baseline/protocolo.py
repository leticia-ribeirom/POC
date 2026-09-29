"""
protocolo.py — Configuração experimental PROPOSTA para o POC I.

Todas as variantes (A: NSGA-II, B: NSGA-II + surrogate e, no POC II,
C: + LLM) devem usar exatamente estes valores, para a comparação ser justa.
"""

PROTOCOLO_POC1 = dict(
    nome_problema="zdt1",   # função do teste de sanidade
    n_var=10,               # variáveis de decisão
    orcamento=300,          # avaliações reais por execução
    tam_pop=20,             # 20 iniciais + 14 gerações x 20 = 300 (sem sobra)
    ref_hv=(1.1, 7.3),      # ponto de referência do HV (regra no README)
)

SEEDS_POC1 = list(range(1, 11))  # 10 repetições para o teste de sanidade
