# 2. Benchmark — a suíte `bbob-biobj` da plataforma COCO

Esta pasta define **o banco de testes do projeto**: quais problemas, em que condições e como a
qualidade é medida. Ela não tem algoritmo de otimização. O NSGA-II (baseline) está em
`../1. baseline`, e as variantes B (surrogate) e C (LLM) vão usar exatamente este mesmo
benchmark.

> **Decidido na reunião de 13/10/2026 com a orientadora:** trocar o benchmark pela suíte
> `bbob-biobj` (Black-Box Optimization Benchmarking, versão bi-objetivo) e medir a qualidade com os
> **indicadores do próprio COCO**. O projeto recomeçou a partir daqui: todas as decisões e todos os
> gráficos foram feitos neste benchmark.

**Conteúdo**

1. [Passo a passo para rodar](#1-passo-a-passo-para-rodar)
2. [O benchmark](#2-o-benchmark)
3. [O cenário experimental](#3-o-cenário-experimental)
4. [Como o COCO mede a qualidade](#4-como-o-coco-mede-a-qualidade)
5. [O piso: busca aleatória](#5-o-piso-busca-aleatória)
6. [Arquivos](#6-arquivos)
7. [Referências](#7-referências)

---

## 1. Passo a passo para rodar

1. Instale o Python 3.10 ou mais novo e as bibliotecas (uma vez só):
   ```bash
   pip install deap numpy scipy matplotlib moocore coco-experiment cocopp cairosvg
   ```
   `coco-experiment` é a plataforma COCO (importada como `cocoex`) e `cocopp` é a ferramenta de
   análise dela.
2. No VS Code, abra a pasta `POC_I` (**File → Open Folder**), entre nesta pasta pelo terminal
   com `cd "2. benchmark"` (as aspas são por causa do espaço) e rode:

| Comando | Tempo | O que faz | Você deve ver |
|---|---|---|---|
| `python funcoes_bbob.py` | segundos | Lista as 55 funções, do que cada uma é feita e o grupo de dificuldade | `55 funções, 15 grupos` |
| `python testes_benchmark.py` | ~10 s | Confere se o benchmark está montado como o protocolo diz | `RESUMO: 4/4 testes do benchmark passaram` |

---

## 2. O benchmark

| Item | Valor | Status |
|---|---|---|
| Suíte | **`bbob-biobj`** da plataforma COCO (TUŠAR et al., 2016; HANSEN et al., 2021) | ✅ |
| Funções | **todas as 55**, cada uma com **2 objetivos** a minimizar | ✅ |
| Região de busca | **[−5, 5]** em cada variável | ✅ |
| Fronteira de Pareto verdadeira | **desconhecida** na maioria das funções | — |

**De que as funções são feitas.** Cada função do `bbob-biobj` junta **duas funções** da suíte
`bbob` de um objetivo: o objetivo 1 é uma e o objetivo 2 é outra. Elas são escolhidas entre 10
funções clássicas, cada uma de uma classe de dificuldade (BROCKHOFF et al., 2022):

| Classe | Funções `bbob` |
|---|---|
| separável | Sphere (f1), Elipsoide separável (f2) |
| moderada | Setor atrativo (f6), Rosenbrock (f8) |
| mal-condicionada | Crista afiada (f13), Soma de potências (f14) |
| multimodal | Rastrigin (f15), Schaffer F7 (f17) |
| fracamente estruturada | Schwefel (f20), Gallagher 101 picos (f21) |

Combinando as 10 duas a duas, saem as 55 funções, que formam **15 grupos** (por exemplo,
"separável + multimodal"). A lista completa está em `resultados/funcoes_bbob_biobj.csv`. Exemplos:
f1 = Sphere × Sphere (a mais fácil), f20 = Sphere × Rastrigin, f55 = Gallagher × Gallagher.

**Instâncias.** Cada função existe em várias **instâncias**: a mesma função deslocada e rotacionada
de formas diferentes. O ótimo muda de lugar em cada instância (o teste B3 confere isso).

**Por que o `bbob-biobj`** (e não a extensão `bbob-biobj-ext`, de 92 funções, que é mais nova):
a original é a mais usada, tem arquivo público de resultados de outros algoritmos e suporte
completo no `cocopp`, inclusive o algoritmo de referência "best 2016". Na versão instalada do
`cocopp` (2.x), o algoritmo de referência da `bbob-biobj-ext` ainda está marcado como "a fazer".

**Vantagem para o LLM (variante C):** como as instâncias são deslocadas e rotacionadas, o LLM não
tem como "saber" a resposta por ter visto a função durante o treinamento (risco de contaminação).

---

## 3. O cenário experimental

Tudo está em **`protocolo.py`**, e vale igual para as três variantes. Legenda: ✅ decidido ·
📝 proposta a confirmar · ⚠️ em aberto.

| Item | Valor | Status |
|---|---|---|
| Dimensões (número de variáveis, D) | **5, 10 e 20** | ✅ |
| Repetições | **instâncias 1 a 15**, uma execução por instância | ✅ |
| Seed do algoritmo | o número da instância (igual para todas as variantes) | ✅ |
| Orçamento | **30 × D** avaliações reais: **150** (D = 5), **300** (D = 10), **600** (D = 20) | 📝 |
| Indicadores | **os do COCO** (seção 4) | ✅ |
| Total | 55 funções × 3 dimensões × 15 instâncias = **2.475 execuções** por algoritmo | — |

**Sobre o orçamento (📝 proposta, falta confirmar com a orientadora).** No COCO o orçamento é
expresso em proporção à dimensão. 30 × D dá 300 avaliações em D = 10, que é a faixa usada na
literatura de otimização cara (KNOWLES, 2006; CHUGH et al., 2018; LI et al., 2023), e deixa o
problema "igualmente caro" nas três dimensões. É esse orçamento curto que simula uma função cara:
o algoritmo só pode consultar a função 30 × D vezes.

**Instâncias como repetições.** Rodar uma vez em cada uma das 15 instâncias equivale a 15
repetições, como manda a prática do COCO (HANSEN et al., 2021).

---

## 4. Como o COCO mede a qualidade

O COCO define como medir o desempenho no `bbob-biobj` (BROCKHOFF et al., 2016). Os algoritmos não
calculam nada: o **observador do COCO** grava cada avaliação, e o **`cocopp`** gera a análise.
O código está em `coco_utils.py`.

1. **O arquivo.** O COCO guarda **todas as soluções não dominadas avaliadas** durante a execução,
   e não só a população final.
2. **Normalização.** Os objetivos são normalizados para que o ponto **ideal** vire (0, 0) e o
   **nadir** vire (1, 1). O hipervolume usa o nadir como ponto de referência.
3. **delta_HV (o indicador).** É a diferença entre o hipervolume de **referência** (o da melhor
   aproximação conhecida da fronteira) e o hipervolume do arquivo:

   > **delta_HV = HV_referência − HV_arquivo** — **menor é melhor**; 0 significa ter alcançado a referência.

   Se nenhuma solução dominar o nadir, o COCO usa a **distância até a região de interesse**, então
   até um algoritmo que ainda está longe recebe uma nota que diferencia "longe" de "muito longe".
4. **Os alvos.** O COCO define **58 alvos** de delta_HV (de 1 até valores bem pequenos).
5. **A medida de desempenho.** É o **número de avaliações** até atingir cada alvo pela primeira vez.
   As curvas **ECDF** mostram, para cada quantidade de avaliações, que fração dos pares
   (função, alvo) já foi atingida.

**Por que isso combina com o projeto:** a pergunta de pesquisa é se o método converge para
soluções melhores **com menos avaliações reais**. A medida do COCO é exatamente essa: quantas
avaliações cada variante precisa para atingir cada nível de qualidade.

---

## 5. O piso: busca aleatória

`busca_aleatoria.py` sorteia 30 × D soluções uniformes em [−5, 5]^D e não aprende nada. Ela é o
**piso** do benchmark: qualquer método que valha a pena precisa ser melhor que ela com o mesmo
orçamento. Ela roda junto com o NSGA-II em `../1. baseline/experimento_baseline.py`.

---

## 6. Arquivos

| Arquivo | O que tem |
|---|---|
| `protocolo.py` | **Todos os valores do protocolo** (benchmark, cenário, população, candidatos da variante B, LLM) |
| `problemas.py` | Transforma um problema do COCO num dicionário simples (função, D, limites) |
| `coco_utils.py` | Roda um algoritmo nos problemas escolhidos com o observador do COCO ligado e lê o delta_HV final |
| `funcoes_bbob.py` | As 55 funções: do que cada uma é feita e o grupo de dificuldade |
| `busca_aleatoria.py` | O piso do benchmark |
| `testes_benchmark.py` | Testes B1 a B4 (abaixo) |
| `resultados/funcoes_bbob_biobj.csv` | Tabela das 55 funções |
| `resultados/relatorio_testes_benchmark.txt` | Saída dos testes |

**Testes (`testes_benchmark.py`):**

| Teste | O que confere | Resultado |
|---|---|---|
| **B1** | 55 × 3 × 15 = 2.475 problemas, todos com 2 objetivos e região [−5, 5] | ✅ |
| **B2** | as 55 funções formam 15 grupos | ✅ |
| **B3** | instâncias diferentes são problemas diferentes (o mesmo x dá valores diferentes) | ✅ 15 valores distintos em 15 instâncias |
| **B4** | o COCO registra exatamente 30 × D avaliações, e a mesma seed reproduz o resultado | ✅ |

---

## 7. Referências

Formato ABNT (NBR 6023). Confira cada referência na fonte original antes de usar no relatório.

BROCKHOFF, D.; AUGER, A.; HANSEN, N.; TUŠAR, T. Using well-understood single-objective functions in
multiobjective black-box optimization test suites. **Evolutionary Computation**, v. 30, n. 2,
p. 165-193, 2022.

BROCKHOFF, D.; TUŠAR, T.; TUŠAR, D.; WAGNER, T.; HANSEN, N.; AUGER, A. **Biobjective performance
assessment with the COCO platform**. arXiv:1605.01746, 2016.

CHUGH, T.; JIN, Y.; MIETTINEN, K.; HAKANEN, J.; SINDHYA, K. A surrogate-assisted reference vector
guided evolutionary algorithm for computationally expensive many-objective optimization.
**IEEE Transactions on Evolutionary Computation**, v. 22, n. 1, p. 129-142, 2018.

HANSEN, N.; AUGER, A.; ROS, R.; MERSMANN, O.; TUŠAR, T.; BROCKHOFF, D. COCO: a platform for
comparing continuous optimizers in a black-box setting. **Optimization Methods and Software**,
v. 36, n. 1, p. 114-144, 2021.

KNOWLES, J. ParEGO: a hybrid algorithm with on-line landscape approximation for expensive
multiobjective optimization problems. **IEEE Transactions on Evolutionary Computation**, v. 10,
n. 1, p. 50-66, 2006.

LI, F.; YANG, Y.; SHANG, Z.; LI, S.; OUYANG, H. Kriging-assisted indicator-based evolutionary
algorithm for expensive multi-objective optimization. **Applied Soft Computing**, v. 147,
art. 110736, 2023.

TUŠAR, T.; BROCKHOFF, D.; HANSEN, N.; AUGER, A. **COCO: the bi-objective black box optimization
benchmarking (bbob-biobj) test suite**. arXiv:1604.00359, 2016.
