# Fase 2 — NSGA-II baseline (variante A do POC)

## Como rodar

```bash
pip install deap numpy scipy matplotlib
python3 nsga2_baseline.py        # uma execução no protocolo proposto, geração a geração
python3 testes_sanidade.py       # testes de correção + gráficos em resultados/
python3 experimento_decisoes.py  # experimento que embasa as decisões propostas
```

## Arquivos

| Arquivo | O que faz |
|---|---|
| `protocolo.py` | **Os valores propostos para o POC I** (função, variáveis, orçamento, população, ref do HV, seeds) |
| `problemas.py` | ZDT1, 2, 3, 4 e 6 (via DEAP), com número de variáveis ajustável e fronteira verdadeira |
| `metricas.py` | Hipervolume e IGD |
| `nsga2_baseline.py` | O NSGA-II, com contador de orçamento e registro por geração |
| `testes_sanidade.py` | Os testes que mostram que o baseline está correto |
| `experimento_decisoes.py` | Calcula o ponto de referência do HV e compara tamanhos de população |

## Decisões propostas para o POC I

> **Status: PROPOSTA A VALIDAR COM A ORIENTADORA.** São escolhas metodológicas do trabalho.
> Cada uma tem uma justificativa abaixo para levar à reunião. Se alguma mudar, basta alterar
> `protocolo.py` e rodar `experimento_decisoes.py` de novo (o ponto de referência depende da função
> e do número de variáveis).

| Decisão | Proposta | Justificativa curta |
|---|---|---|
| Função do teste de sanidade | **ZDT1** | Fronteira convexa e contínua, o caso mais simples; o objetivo do POC I é validar o pipeline, não testar dificuldades |
| Número de variáveis | **10** | Faixa usada na literatura de otimização cara; com 300 amostras, 10 dimensões dão ao Random Forest da Fase 3 uma chance realista de aprender |
| Orçamento de avaliações reais | **300** | Mesmo valor de SAEAs de referência testados em ZDT/DTLZ |
| Tamanho da população | **20** | Melhor IGD no experimento, empatado com 12; divide 300 exatamente (sem sobra) |
| Ponto de referência do HV | **(1.1, 7.3)** | 10% pior que o pior ponto das frentes aleatórias iniciais; qualquer melhoria sobre a amostragem aleatória aparece no HV |
| Repetições no POC I | **10 seeds (1 a 10)** | O PDF pede "poucas repetições" para o teste de sanidade; o POC II terá mais |

### 1. Função: ZDT1

O PDF pede o teste de sanidade em "uma única função" de um "subconjunto da suíte ZDT/DTLZ".
O ZDT1 é o caso mais simples: 2 objetivos, fronteira convexa e contínua. Se o pipeline
falhar no ZDT1, ele está errado; se funcionar, dá para passar às funções mais difíceis.

**Limitação a declarar:** por ser fácil, o ZDT1 pode esconder diferenças entre as variantes.
Por isso ele serve para validar o pipeline, não para tirar conclusões.

**Para o POC II (sugestão, não implementado):** ZDT1, ZDT2 e ZDT3 (fronteira convexa, côncava
e desconexa) mais uma DTLZ com 3 objetivos (DTLZ2, a mais regular). O ZDT4 e a DTLZ1 são
multimodais e podem entrar se houver tempo.

### 2. Número de variáveis: 10 (em vez das 30 originais)

O ZDT1 original usa 30 variáveis. Trabalhos de otimização cara costumam usar 10: um estudo de 2023
com Kriging usa cinco ZDT e sete DTLZ com 10 variáveis e no máximo 300 avaliações reais; outro
trabalho recente também testa instâncias de 10 variáveis com 300 avaliações. O motivo prático é que,
com poucas centenas de avaliações, é difícil um modelo substituto aprender uma função de 30 dimensões.

A fronteira de Pareto verdadeira **não muda** com o número de variáveis (ela depende só de f1), então
o IGD continua comparável. **Declarar no relatório** que é uma adaptação do ZDT1 original.

### 3. Orçamento: 300 avaliações reais

A literatura de algoritmos assistidos por surrogate trabalha com algumas centenas de avaliações:
- ParEGO (Knowles, 2006): 100 e 250 (ou 260) avaliações;
- K-RVEA (Chugh et al., 2018): 300 avaliações;
- o estudo de 2023 com Kriging citado acima: 300 avaliações em ZDT e DTLZ.

300 está nessa faixa e coincide com trabalhos que usam exatamente ZDT/DTLZ.
**Confira esses números nos artigos completos antes de citá-los** (foram verificados em resumos e trechos).

### 4. População: 20

Rodei o NSGA-II com todas as populações múltiplas de 4 que dividem 300 exatamente (12, 20, 60 e 100),
30 seeds cada, no ZDT1 com 10 variáveis (`resultados/D1_tamanho_populacao.png`):

| População | Gerações | IGD final (média ± desvio) |
|---|---|---|
| 12 | 24 | 0.672 ± 0.203 |
| **20** | **14** | **0.681 ± 0.183** |
| 60 | 4 | 1.069 ± 0.234 |
| 100 | 2 | 1.247 ± 0.226 |

- 12 e 20 **empatam** (teste de Mann-Whitney, p = 0.70).
- 20 é **claramente melhor** que 60 (p ≈ 10⁻⁷). Populações grandes gastam o orçamento em poucas gerações.
- Entre as empatadas, 20 mantém mais pontos na frente final, o que cobre melhor a fronteira.

**Por que ajustar a população do baseline é justo:** um baseline mal configurado faria o surrogate
parecer melhor do que é. Escolher a melhor população para o NSGA-II puro torna a comparação mais honesta.
A mesma população deve ser usada nas variantes B e C.

### 5. Ponto de referência do HV: (1.1, 7.3)

**Regra:** 10% pior que o pior valor de cada objetivo nas frentes **iniciais** (aleatórias) de 30 execuções,
arredondado para cima. O pior observado foi f1 = 0.990 e f2 = 6.565, o que dá (1.1, 7.3).

**Por quê:**
- Com a referência convencional (1.1, 1.1), quase todas as soluções do regime de 300 avaliações ficam fora da
  "cerca" e o HV fica perto de zero (0.078 em média), sem distinguir as execuções.
- Com (1.1, 7.3), toda solução melhor que a amostragem aleatória conta. O HV passa a medir quanto cada
  variante melhorou em relação ao ponto de partida.
- A regra usa só a população inicial aleatória, que será **a mesma** para as três variantes (mesmas seeds).
  Então ela não favorece nenhuma delas.

**Cuidado:** a referência vale só para ZDT1 com 10 variáveis. Mudou a função ou o número de variáveis,
recalcule com `experimento_decisoes.py`. Os HVs só são comparáveis com a mesma referência.

### 6. Repetições: 10

O PDF diz que o POC I terá "poucas repetições, apenas para validar que o pipeline converge". Dez seeds
dão uma ideia da variação sem virar um estudo estatístico, que fica para o POC II.

## Resultados dos testes

T1 a T5 usam a configuração do artigo original do NSGA-II (pop 100, 25.000 avaliações, 30 variáveis),
para comparar com o comportamento conhecido do algoritmo.

- **T1 convergência (PASSOU):** no ZDT1, IGD final 0.0050 e HV 0.869 (99,1% do máximo teórico).
- **T2 curva de HV (PASSOU):** HV sobe de 0 a 0.869. Há quedas minúsculas (maior: 0.0005), esperadas quando o crowding descarta um ponto não dominado.
- **T3 orçamento (PASSOU):** o contador nunca passa do limite e bloqueia uma avaliação a mais.
- **T4 reprodutibilidade (PASSOU):** mesma seed dá resultado idêntico; seed diferente, resultado diferente.
- **T5 demais ZDT:** IGD entre 0.005 e 0.008 em todas. As frentes coincidem com as fronteiras verdadeiras.
- **T6 protocolo proposto do POC I:** ZDT1, 10 variáveis, 300 avaliações, pop 20, 10 seeds:
  **IGD 0.739 ± 0.193 e HV 6.507 ± 0.177**. Estes são os números do baseline que a Fase 3 precisa superar.

## Onde cada passo do NSGA-II está no código (`rodar_nsga2`)

| Passo (da nossa aula) | No código |
|---|---|
| População inicial aleatória, avaliada | `pop = tb.populacao(...)` e o laço com `tb.evaluate` |
| Rank + crowding da população inicial | `pop = tb.select(pop, len(pop))` |
| Seleção de pais por torneio | `tools.selTournamentDCD(pop, len(pop))` |
| Cruzamento SBX e mutação polinomial | `tb.mate(...)`, `tb.mutate(...)` |
| Avaliação real dos filhos | `ind.fitness.values = tb.evaluate(ind)` |
| Sobrevivência: pais + filhos → N melhores | `pop = tb.select(pop + filhos, tam_pop)` |
| Parada pelo orçamento | `while avaliar.restante >= tam_pop` |

**Onde a Fase 3 vai mexer:** só no trecho "variação + avaliação real dos filhos".
O surrogate vai entrar entre gerar os filhos e avaliá-los. O resto fica igual.

## Parâmetros fixos do algoritmo e de onde vêm

Probabilidade de cruzamento 0.9, mutação 1/n por variável, eta_c = eta_m = 20:
são os valores do artigo original do NSGA-II (Deb et al., 2002).

## Um detalhe para saber explicar

Quando um par de filhos não sofre cruzamento e a mutação não altera nada, o filho é
idêntico ao pai, mas ainda assim é avaliado de novo (gasta orçamento). É o comportamento
padrão do DEAP e não muda a comparação entre variantes, desde que todas façam igual.

## Arquivo de avaliações

Toda avaliação real fica em `resultado["arquivo_X"]` (variáveis) e `resultado["arquivo_F"]`
(objetivos). No baseline isso é só registro; na Fase 3 é o conjunto de treino do Random Forest.

## Referências usadas nas justificativas

- Deb, K. et al. (2002). NSGA-II. *IEEE TEVC*, 6(2). (já está na proposta)
- Zitzler, E., Deb, K., Thiele, L. (2000). *Evolutionary Computation*, 8(2). (já está na proposta)
- Knowles, J. (2006). ParEGO. *IEEE TEVC*, 10(1), 50–66.
- Chugh, T., Jin, Y., Miettinen, K., Hakanen, J., Sindhya, K. (2018). K-RVEA. *IEEE TEVC*.
- Kriging-assisted indicator-based evolutionary algorithm for expensive multi-objective optimization (2023).
  *Applied Soft Computing*. https://www.sciencedirect.com/science/article/abs/pii/S1568494623007548
