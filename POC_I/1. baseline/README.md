# Fase 2 — Baseline: NSGA-II no `bbob-biobj`

Esta pasta contém a **variante A** do projeto: o NSGA-II puro (DEB et al., 2002), implementado
em Python com a biblioteca DEAP (FORTIN et al., 2012) e rodado no benchmark do projeto, a suíte
`bbob-biobj` do COCO (definida em `../fase2b_benchmark`). Ela é a referência contra a qual o
NSGA-II + surrogate (variante B) e o NSGA-II + surrogate + LLM (variante C) serão comparados.

> **Reunião de 13/10/2026 com a orientadora:** o benchmark passou a ser o `bbob-biobj`, os
> indicadores passaram a ser os do COCO e todo o projeto, inclusive o LLM, passou para o POC I.
> O baseline foi refeito do zero nesse cenário: **todos os testes, gráficos e decisões desta pasta
> foram feitos no `bbob-biobj`.**

**Conteúdo**

1. [Passo a passo para rodar](#1-passo-a-passo-para-rodar)
2. [O algoritmo e sua configuração](#2-o-algoritmo-e-sua-configuração)
3. [Testes de correção](#3-testes-de-correção)
4. [Resultados do baseline](#4-resultados-do-baseline)
5. [Decisões tomadas no `bbob-biobj`](#5-decisões-tomadas-no-bbob-biobj)
6. [Como o código está organizado](#6-como-o-código-está-organizado)
7. [Detalhes para saber explicar](#7-detalhes-para-saber-explicar)
8. [Referências](#8-referências)

---

## 1. Passo a passo para rodar

### Passo 1 — Instalar (uma vez só)

**Python 3.10 ou mais novo** (testado com 3.11) e **VS Code** com a extensão **Python**.

### Passo 2 — Abrir a pasta `fase2_baseline` no VS Code (File → Open Folder)

Ela precisa estar ao lado da pasta `fase2b_benchmark` (como vem no zip): os scripts daqui buscam
o benchmark lá.

### Passo 3 — Ambiente virtual e bibliotecas

| Windows | Mac / Linux |
|---|---|
| `python -m venv .venv` | `python3 -m venv .venv` |
| `.venv\Scripts\activate` | `source .venv/bin/activate` |

Depois, nos dois sistemas:

```bash
pip install deap numpy scipy matplotlib moocore coco-experiment cocopp cairosvg
```

`Ctrl+Shift+P` → **Python: Select Interpreter** → escolha a opção com `.venv`.

### Passo 4 — Rodar

| # | Comando | Tempo | O que faz |
|---|---|---|---|
| 1 | `python nsga2_baseline.py` | < 1 s | Demonstração: uma execução (f1, D = 10, instância 1), geração a geração |
| 2 | `python testes_baseline.py` | ~1 min | Testes de correção T1 a T6 (seção 3) |
| 3 | `python experimento_baseline.py` | ~5 min | **O baseline completo**: NSGA-II × busca aleatória nas 2.475 execuções, mais a análise do COCO |
| 4 | `python experimento_populacao.py` | ~10 min | Decisão da população (seção 5.1) |
| 5 | `python experimento_amostra_inicial.py` | ~6 min | Decisão da amostra inicial (seção 5.2) |
| — | `python grafico_convergencia.py`, `grafico_populacao.py`, `grafico_amostra_inicial.py` | segundos | Refazem só os gráficos |

### Passo 5 — Conferir

| Script | Você deve ver |
|---|---|
| `nsga2_baseline.py` | gerações 0 a 14, 300 avaliações, e no fim **delta_HV final 0.258** |
| `testes_baseline.py` | **`RESUMO: 6/6 testes automáticos passaram`** |
| `experimento_baseline.py` | a tabela da seção 4 e, na pasta `ppdata/`, o `index.html` da análise do COCO |

As pastas `exdata/` (dados brutos do COCO) e `ppdata/` (análise do `cocopp`) são recriadas a cada
execução e **não vão para o git nem para o zip**.

---

## 2. O algoritmo e sua configuração

O protocolo (benchmark, dimensões, instâncias, orçamento) está em `../fase2b_benchmark`. Aqui
está o que é do **algoritmo**. Legenda: ✅ decidido · ⚠️ em aberto.

**Comum às três variantes:**

| Parâmetro | Valor | Origem |
|---|---|---|
| População | **20** | ✅ testada no `bbob-biobj` (seção 5.1) |
| Amostra inicial | **20** (igual à população) | ⚠️ testada no `bbob-biobj` (seção 5.2); decisão final na Fase 3 |
| Seleção de pais | torneio binário (`selTournamentDCD`) | NSGA-II |
| Cruzamento | SBX, probabilidade 0.9, eta 20 | DEB et al. (2002) |
| Mutação | polinomial, probabilidade 1/D por variável, eta 20 | DEB et al. (2002) |
| Sobrevivência | `selNSGA2` (frente de Pareto + crowding distance) | NSGA-II |
| Parada | quando o orçamento (30 × D) acaba | protocolo |
| Gerações | **consequência** do orçamento: 6 + 1 parcial (D = 5), 14 (D = 10), 29 (D = 20) | — |

**Geração final parcial.** Em D = 5 o orçamento é 150: 20 iniciais + 6 gerações de 20 = 140, e
sobrariam 10. A última geração avalia só os filhos que cabem no orçamento (10), e o orçamento é
usado por inteiro.

**Específico da variante B (surrogate):** cada geração gera **muitos filhos**, e o Random Forest
escolhe os **20** mais promissores para a avaliação real (seção 5.3).

**Específico da variante C (LLM):** modelo acessado por **API paga do Claude (Anthropic)**
(✅ decidido em 13/10/2026). Em aberto: modelo exato, conteúdo do prompt, frequência das chamadas
e se o LLM soma ou substitui candidatos.

---

## 3. Testes de correção

`testes_baseline.py`. Como a fronteira verdadeira do `bbob-biobj` não é conhecida, a correção é
conferida contra a **referência do COCO** (a melhor aproximação conhecida da fronteira).

| Teste | O que confere | Resultado |
|---|---|---|
| **T1** convergência | com 20.000 avaliações, o NSGA-II chega perto da referência nas funções mais fáceis (f1, f2, f11 em D = 5), e melhora quando o orçamento cresce | ✅ delta_HV 0.0018, 0.0004 e 0.0004 |
| **T2** orçamento | usa exatamente 150, 300 e 600 avaliações (com a geração parcial em D = 5) e bloqueia excessos | ✅ |
| **T3** reprodutibilidade | mesma seed → resultado idêntico; seed diferente → resultado diferente | ✅ |
| **T4** amostra inicial | `n_inicial` = 20 é o NSGA-II clássico; `n_inicial` maior respeita o orçamento | ✅ |
| **T5** COCO | o observador do COCO conta as mesmas avaliações que o contador do NSGA-II | ✅ |
| **T6** melhor que o acaso | em D = 10, instância 1, o NSGA-II vence a busca aleatória nas 55 funções | ✅ 100% das funções |

**Gráfico `resultados/T1_convergencia_orcamento_grande.png`:** com muitas avaliações, o delta_HV
cai até perto de 0,001, então o algoritmo está correto. A linha tracejada marca o orçamento do
projeto (150 em D = 5): ali o NSGA-II ainda está longe. **Esse é o problema que o projeto ataca.**

---

## 4. Resultados do baseline

55 funções × 3 dimensões × 15 instâncias = **2.475 execuções** para cada algoritmo
(`experimento_baseline.py`; dados em `resultados/bbob_finais.csv` e `resultados/bbob_resumo.txt`).

### 4.1 delta_HV final (menor é melhor)

| D | Orçamento | NSGA-II: mediana (quartis 25%–75%) | Busca aleatória: mediana | NSGA-II melhor que a aleatória | NSGA-II com delta_HV ≤ 0.1 |
|---|---|---|---|---|---|
| 5 | 150 | **0.271** (0.148–0.448) | 0.384 | 78% das execuções | 16% |
| 10 | 300 | **0.292** (0.154–0.463) | 0.594 | 97% | 15% |
| 20 | 600 | **0.306** (0.198–0.503) | 0.727 | 100% | 10% |

Wilcoxon pareado (mesma função, dimensão e instância), NSGA-II < aleatória: p ≈ 0 (abaixo da
precisão numérica).

**Leitura:**
- **O NSGA-II funciona no benchmark:** é muito melhor que sortear soluções, e a vantagem cresce
  com a dimensão (em D = 20, vence em 100% das execuções).
- **Mas fica longe da referência:** a mediana de delta_HV fica perto de 0.3, e só 10% a 16% das
  execuções chegam a 0.1. Há bastante espaço para o surrogate melhorar, que é a pergunta da Fase 3.
- **A dificuldade aumenta com a dimensão**, mesmo com o orçamento proporcional (30 × D).

### 4.2 Por grupo de funções (D = 10, mediana de delta_HV)

| Grupo | NSGA-II | Aleatória |
|---|---|---|
| separável + separável | 0.184 | 0.393 |
| separável + moderada | **0.122** | 0.423 |
| separável + mal-condicionada | 0.279 | 0.512 |
| separável + multimodal | 0.320 | 0.596 |
| separável + fracamente estruturada | 0.302 | 0.560 |
| moderada + moderada | 0.136 | 0.471 |
| moderada + mal-condicionada | 0.271 | 0.627 |
| moderada + multimodal | 0.352 | 0.566 |
| moderada + fracamente estruturada | 0.219 | 0.703 |
| mal-condicionada + mal-condicionada | 0.290 | 0.502 |
| mal-condicionada + multimodal | 0.382 | 0.606 |
| mal-condicionada + fracamente estruturada | **0.419** | 0.688 |
| multimodal + multimodal | 0.397 | 0.646 |
| multimodal + fracamente estruturada | 0.384 | 0.707 |
| fracamente estruturada + fracamente estruturada | 0.366 | 0.795 |

As combinações com funções **multimodais** e **fracamente estruturadas** são as mais difíceis; as
com funções **separáveis e moderadas** são as mais fáceis. Faz sentido: muitos ótimos locais
atrapalham uma busca com poucas avaliações.

### 4.3 Gráficos

- **`resultados/B2_convergencia_bbob.png`** — mediana de delta_HV ao longo do orçamento, NSGA-II ×
  busca aleatória, para D = 5, 10 e 20. **É o gráfico mais fácil de ler.** As curvas se separam
  cedo e a distância aumenta com a dimensão.
- **`resultados/B1_ecdf_05D.png`, `B1_ecdf_10D.png`, `B1_ecdf_20D.png`** — as curvas ECDF oficiais
  do COCO, com o **"best 2016"** (o melhor desempenho conhecido entre os algoritmos do arquivo do
  COCO) como referência. **Como ler:** o eixo horizontal é log10(avaliações / D); o orçamento
  (30 × D) termina em **log10(30) ≈ 1,5**, e é só até ali que há dados. A linha horizontal depois
  disso apenas prolonga o último valor, e a linha que sobe no fim só liga a curva ao nome do
  algoritmo. No fim do orçamento, a fração de alvos atingidos é de cerca de 12% para o NSGA-II em
  D = 10 (o "best 2016" está um pouco acima) e de cerca de 10% em D = 20 (o "best 2016" chega a uns
  15%). Valores lidos no gráfico, aproximados.
- **`ppdata/index.html`** — a análise completa do `cocopp` (abrir no navegador depois de rodar).

---

## 5. Decisões tomadas no `bbob-biobj`

### 5.1 População: 20 ✅

`experimento_populacao.py`: populações de 8 a 100, 2.475 execuções cada
(`resultados/bbob_populacao.txt`, gráfico **`resultados/P1_populacao_bbob.png`**). Mediana de
delta_HV final (menor é melhor):

| D | Orçamento | pop 8 | pop 12 | **pop 20** | pop 40 | pop 60 | pop 100 |
|---|---|---|---|---|---|---|---|
| 5 | 150 | **0.238** | 0.245 | 0.271 | 0.330 | 0.358 | 0.385 |
| 10 | 300 | 0.303 | 0.298 | **0.292** | 0.366 | 0.438 | 0.523 |
| 20 | 600 | 0.362 | 0.332 | **0.306** | 0.350 | 0.407 | 0.525 |

Teste de Wilcoxon pareado (mesma função e instância) contra a população 20:

- **Populações maiores (40, 60 e 100) são piores em todas as dimensões** (p < 10⁻²⁸). Com orçamento
  apertado, elas gastam as avaliações em poucas gerações: com 100, são só 2 gerações em D = 10.
- **D = 10:** a população 20 empata com a 12 (p = 0.96) e é um pouco melhor que a 8 (p = 0.04).
- **D = 20:** a população 20 é a melhor de todas (p < 10⁻⁷ contra a 8 e a 12).
- **D = 5:** populações menores são um pouco melhores (0.238 com 8 e 0.271 com 20; p < 10⁻⁶). Com
  só 150 avaliações, mais gerações compensam.

**Decisão: 20 em todas as dimensões.** É a melhor ou empata em D = 10 e D = 20, a diferença em
D = 5 é pequena, e uma população única deixa o protocolo mais simples e igual para as três
variantes. Ajustar a população por dimensão (por exemplo, 12 em D = 5) fica como ponto a discutir
com a orientadora.

**20 é baixo para os padrões do NSGA-II** (o artigo original usa 100), mas é consequência do
orçamento apertado: cada indivíduo a mais é uma geração a menos. Por isso, **a exploração maior
fica a cargo da variante B** (seção 5.3).

### 5.2 Amostra inicial: 20 por enquanto ⚠️

A amostra inicial são as soluções aleatórias avaliadas antes da evolução. Ela gasta orçamento e,
na Fase 3, é o **primeiro conjunto de treino do Random Forest**: com 20 exemplos em 10 ou 20
dimensões, o modelo começa com pouca informação. O K-RVEA usa 11D − 1 soluções iniciais (CHUGH
et al., 2018).

`experimento_amostra_inicial.py` mede o efeito no NSGA-II puro (população 20), 2.475 execuções
por opção (`resultados/bbob_amostra_inicial.txt`, gráfico
**`resultados/A1_amostra_inicial_bbob.png`**). Mediana de delta_HV final:

| D | Orçamento | 20 (clássico) | 40 | 11D − 1 (K-RVEA) |
|---|---|---|---|---|
| 5 | 150 | 0.271 | **0.252** | 0.260 (54) |
| 10 | 300 | 0.292 | **0.280** | 0.298 (109) |
| 20 | 600 | 0.306 | **0.299** | 0.310 (219) |

Wilcoxon pareado contra a amostra 20:

- **40 é um pouco melhor nas três dimensões** (p = 2 × 10⁻⁴, 5 × 10⁻³ e 2 × 10⁻⁶), mas a diferença é
  pequena (0,01 a 0,02).
- **11D − 1 empata com 20 em D = 10 e D = 20** (p = 0.15 e 0.14), mesmo gastando mais de um terço do
  orçamento na amostra, e é um pouco melhor em D = 5.

**Leitura:** no NSGA-II puro, uma amostra inicial maior **não atrapalha**. Isso abre espaço para a
Fase 3 usar uma amostra maior, que dá mais dados ao Random Forest sem prejudicar o baseline.
**O valor continua 20 no protocolo** até a decisão da Fase 3, que vai testar estas opções já com o
surrogate. Se mudar, muda para as três variantes.

### 5.3 Candidatos por geração da variante B: 100, 200 ou 500 ✅ (valor final na Fase 3)

Como aumentar a população piora o resultado (seção 5.1), a exploração foi levada para a variante
B: em cada geração, ela gera **muitos candidatos** com cruzamento e mutação, sem gastar orçamento,
e o Random Forest escolhe os 20 que serão avaliados de verdade (figura do funil em
`../documentos/figuras/F1_funil_metodo.png`). A Fase 3 vai comparar **100, 200 e 500** candidatos
(o melhor de 5, de 10 e de 25), e o vencedor vira o valor final (`N_CANDIDATOS_OPCOES` em
`../fase2b_benchmark/protocolo.py`). É a mesma ideia dos algoritmos assistidos por surrogate da
literatura, que exploram bastante no modelo e avaliam poucas soluções de verdade; o K-RVEA, por
exemplo, reavalia 5 soluções a cada atualização do modelo (CHUGH et al., 2018). Em aberto: regra
de pré-seleção, configuração e frequência de retreino do Random Forest.

---

## 6. Como o código está organizado

| Arquivo | O que tem |
|---|---|
| `nsga2_baseline.py` | O NSGA-II, com contador de orçamento e registro por geração |
| `testes_baseline.py` | Testes de correção T1 a T6 |
| `experimento_baseline.py` | **O experimento do baseline** (NSGA-II × busca aleatória) + `cocopp` |
| `grafico_convergencia.py` | Gráfico B2 (convergência dentro do orçamento) |
| `experimento_populacao.py`, `grafico_populacao.py` | Decisão da população (seção 5.1, gráfico P1) |
| `experimento_amostra_inicial.py`, `grafico_amostra_inicial.py` | Decisão da amostra inicial (seção 5.2, gráfico A1) |
| `../fase2b_benchmark/` | Protocolo, problemas, COCO, busca aleatória |

```
../fase2b_benchmark/                 fase2_baseline/
  protocolo.py ──┐
  problemas.py ──┼──► nsga2_baseline.py ──► experimento_baseline.py ──► cocopp (ECDF, B1)
  coco_utils.py ─┤                                     └──► grafico_convergencia.py (B2)
  busca_aleatoria.py ┘
```

### Onde cada passo do NSGA-II está (função `rodar_nsga2`)

| Passo | Código |
|---|---|
| 1. Amostra inicial aleatória (`n_inicial`), avaliada | `amostra = tb.populacao(n=n_inicial)` + `tb.evaluate` |
| 2. As `tam_pop` melhores da amostra viram a população | `pop = tb.select(amostra, tam_pop)` |
| 3. Seleção de pais por torneio | `tools.selTournamentDCD(pop, len(pop))` |
| 4. Cruzamento SBX e mutação polinomial | `tb.mate(...)`, `tb.mutate(...)` |
| 5. Avaliação real dos filhos (todos, ou os que cabem no orçamento) | `filhos[:n_avaliar]` + `tb.evaluate` |
| 6. Sobrevivência: pais + filhos → N melhores | `pop = tb.select(pop + filhos, tam_pop)` |
| 7. Parada pelo orçamento | `while avaliar.restante > 0` |

**Onde a variante B vai mexer:** entre os passos 4 e 5 (gerar 100, 200 ou 500 filhos, e o Random
Forest escolhe 20). **Onde a variante C vai mexer:** no passo 4 (o LLM também propõe candidatos).

---

## 7. Detalhes para saber explicar

- **O contador de avaliações** (`ContadorAvaliacoes`) embrulha a função: conta cada chamada,
  bloqueia qualquer avaliação além do orçamento e guarda cada par (x, f(x)) no arquivo, que será o
  conjunto de treino do Random Forest. O COCO conta as avaliações de forma independente, e o teste
  T5 confere que as duas contagens batem.
- **Seed = número da instância:** a variante A e a variante B partem da mesma amostra inicial em
  cada instância, então a diferença no resultado vem do método.
- **O NSGA-II não calcula a qualidade:** quem mede é o observador do COCO, igual para todas as
  variantes.
- **`del f1.fitness.values`:** o filho nasce como cópia do pai; depois de modificado, a nota do pai
  não vale mais e precisa ser apagada para forçar uma avaliação nova.
- **`pop + filhos`** é o elitismo: pais competem com filhos, então uma solução boa nunca se perde.

---

## 8. Referências

Formato ABNT (NBR 6023). Confira cada referência na fonte original antes de usar no relatório.

BROCKHOFF, D.; TUŠAR, T.; TUŠAR, D.; WAGNER, T.; HANSEN, N.; AUGER, A. **Biobjective performance
assessment with the COCO platform**. arXiv:1605.01746, 2016.

CHUGH, T.; JIN, Y.; MIETTINEN, K.; HAKANEN, J.; SINDHYA, K. A surrogate-assisted reference vector
guided evolutionary algorithm for computationally expensive many-objective optimization.
**IEEE Transactions on Evolutionary Computation**, v. 22, n. 1, p. 129-142, 2018.

DEB, K.; PRATAP, A.; AGARWAL, S.; MEYARIVAN, T. A fast and elitist multiobjective genetic
algorithm: NSGA-II. **IEEE Transactions on Evolutionary Computation**, v. 6, n. 2, p. 182-197,
2002.

FORTIN, F.-A.; DE RAINVILLE, F.-M.; GARDNER, M.-A.; PARIZEAU, M.; GAGNÉ, C. DEAP: evolutionary
algorithms made easy. **Journal of Machine Learning Research**, v. 13, p. 2171-2175, 2012.

HANSEN, N.; AUGER, A.; ROS, R.; MERSMANN, O.; TUŠAR, T.; BROCKHOFF, D. COCO: a platform for
comparing continuous optimizers in a black-box setting. **Optimization Methods and Software**,
v. 36, n. 1, p. 114-144, 2021.

TUŠAR, T.; BROCKHOFF, D.; HANSEN, N.; AUGER, A. **COCO: the bi-objective black box optimization
benchmarking (bbob-biobj) test suite**. arXiv:1604.00359, 2016.

WILCOXON, F. Individual comparisons by ranking methods. **Biometrics Bulletin**, v. 1, n. 6,
p. 80-83, 1945.
