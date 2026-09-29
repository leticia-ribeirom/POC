# Fase 2 — NSGA-II baseline

Esta pasta contém a **variante A** do POC: o NSGA-II puro (DEB et al., 2002a), implementado em
Python com a biblioteca DEAP (FORTIN et al., 2012).
Ela é a referência contra a qual o NSGA-II + surrogate (Fase 3) e, no POC II, o
NSGA-II + surrogate + LLM serão comparados.

**Conteúdo deste README**

1. [Passo a passo para rodar](#1-passo-a-passo-para-rodar)
2. [Decisões do protocolo](#2-decisões-do-protocolo)
3. [Resultados](#3-resultados)
4. [Como o código está organizado](#4-como-o-código-está-organizado)
5. [Detalhes para saber explicar](#5-detalhes-para-saber-explicar)
6. [Referências](#6-referências)

---

## 1. Passo a passo para rodar

### Passo 1 — Instalar o que falta (uma vez só)

- **Python 3.10 ou mais novo** (testado com 3.11). No Windows, marque "Add Python to PATH" na instalação.
- **VS Code** com a extensão **Python** (da Microsoft).

### Passo 2 — Abrir a pasta no VS Code

1. Descompacte o zip.
2. No VS Code: **File → Open Folder** → escolha a pasta **`poc_nsga2`** (não a pasta de fora).

### Passo 3 — Criar o ambiente virtual e instalar as bibliotecas

Abra o terminal (**Terminal → New Terminal**) e rode:

| Windows | Mac / Linux |
|---|---|
| `python -m venv .venv` | `python3 -m venv .venv` |
| `.venv\Scripts\activate` | `source .venv/bin/activate` |
| `pip install deap numpy scipy matplotlib moocore` | `pip install deap numpy scipy matplotlib moocore` |

Deve aparecer `(.venv)` no começo da linha do terminal.

Depois: `Ctrl+Shift+P` (Mac: `Cmd+Shift+P`) → **Python: Select Interpreter** → escolha a opção com `.venv`.

> **Erro no Windows ao ativar?** Rode `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, responda "S" e tente de novo.

### Passo 4 — Rodar os scripts, nesta ordem

No Mac, troque `python` por `python3` se for preciso.

| # | Comando | Tempo | O que faz |
|---|---|---|---|
| 1 | `python nsga2_baseline.py` | < 1 s | Uma execução no protocolo proposto, geração a geração |
| 2 | `python testes_sanidade.py` | ~1 min | Testa se a implementação está correta e gera os gráficos |
| 3 | `python experimento_decisoes.py` | ~1–2 min | Experimento que embasa as decisões da seção 2 |
| 4 | `pip install pymoo` e depois `python comparacao_pymoo.py` | ~1–2 min | *(opcional)* Compara com o NSGA-II de outra biblioteca |

Também dá para abrir o arquivo e clicar no botão **▶ Run Python File**, no canto superior direito.

### Passo 5 — Conferir se deu certo

| Script | Você deve ver |
|---|---|
| `nsga2_baseline.py` | 15 linhas (gerações 0 a 14), avaliações indo de 20 a 300, e no fim **HV 6.154 e IGD 1.174** |
| `testes_sanidade.py` | Última linha: **`RESUMO: 4/4 testes automáticos passaram`** |
| `experimento_decisoes.py` | Ponto de referência **(1.1, 7.3)** e a tabela de populações |
| todos | Gráficos (`.png`) e relatórios (`.txt`) na pasta **`resultados/`** |

Os números devem ser iguais porque as seeds são fixas. Com versões diferentes das bibliotecas,
as últimas casas decimais podem variar um pouco; o importante é os 4 testes passarem.

---

## 2. Decisões do protocolo

> ⚠️ **Status: proposta a validar com a orientadora.** São escolhas metodológicas do trabalho,
> cada uma com a justificativa abaixo. Todos os valores ficam em **`protocolo.py`**: se algum mudar,
> altere só esse arquivo. Se mudar a função ou o número de variáveis, rode `experimento_decisoes.py`
> de novo para recalcular o ponto de referência.

### Resumo

| Decisão | Valor proposto | Justificativa em uma linha |
|---|---|---|
| Função (benchmark) | **ZDT1** | O caso mais simples; o POC I só precisa validar o pipeline |
| Número de variáveis | **10** | Usado na literatura de otimização cara (LI et al., 2023); o surrogate precisa de dados suficientes |
| Orçamento | **300 avaliações reais** | Valor usado por SAEAs testados em ZDT/DTLZ (CHUGH et al., 2018; LI et al., 2023) |
| População | **20** | Melhor resultado no nosso experimento; divide 300 exatamente |
| Ponto de referência do HV | **(1.1, 7.3)** | Qualquer melhoria em relação ao ponto de partida aleatório aparece no HV |
| Repetições | **10 seeds (1 a 10)** | O PDF pede "poucas repetições" no POC I |

### 2.1 Função: ZDT1

- **O que é:** função da suíte ZDT (ZITZLER; DEB; THIELE, 2000), com 2 objetivos e fronteira
  convexa e contínua (f2 = 1 − √f1).
- **Por quê:** o PDF pede o teste de sanidade em uma única função. O ZDT1 é o caso mais simples.
  Se o pipeline falhar nele, está errado; se funcionar, dá para seguir para funções mais difíceis.
- **Limitação a declarar:** por ser fácil, pode esconder diferenças entre as variantes. Serve para
  validar o pipeline, não para tirar conclusões.
- **Para o POC II (sugestão):** ZDT1, ZDT2 e ZDT3 (convexa, côncava, desconexa) + DTLZ2
  (DEB et al., 2002b), com 3 objetivos.

### 2.2 Número de variáveis: 10 (o ZDT1 original tem 30)

- **Por quê:**
  1. Trabalhos de otimização cara com ZDT/DTLZ usam 10 variáveis com 300 avaliações, como
     Li et al. (2023).
  2. Com no máximo 300 exemplos, um surrogate aprende muito melhor em 10 dimensões do que em 30
     (maldição da dimensionalidade).
  3. A fronteira verdadeira **não muda** (depende só de f1), então o IGD continua válido.
  4. No POC II, vetores menores ocupam menos espaço no prompt do LLM.
- **Declarar no relatório:** é uma adaptação do ZDT1 original.
- **Alternativa:** testar 10 e 30 variáveis no POC II.

### 2.3 Orçamento: 300 avaliações reais

- **Por quê:** a literatura de otimização cara trabalha com algumas centenas de avaliações:
  - ParEGO (KNOWLES, 2006): 100 e 250 avaliações;
  - K-RVEA (CHUGH et al., 2018): 300 avaliações;
  - algoritmo evolutivo baseado em indicador assistido por Kriging (LI et al., 2023):
    300 avaliações em ZDT e DTLZ com 10 variáveis.
- **Cuidado:** confira esses números nos artigos completos antes de citar
  (foram verificados em resumos e trechos).

### 2.4 População: 20

Rodamos o NSGA-II com as populações que são múltiplas de 4 (exigência do DEAP) e dividem 300
exatamente, 30 seeds cada (gráfico `resultados/D1_tamanho_populacao.png`):

| População | Gerações | IGD final (média ± desvio) | Conclusão |
|---|---|---|---|
| 12 | 24 | 0.672 ± 0.203 | empata com 20 |
| **20** | **14** | **0.681 ± 0.183** | **proposta** |
| 60 | 4 | 1.069 ± 0.234 | pior que 20 |
| 100 | 2 | 1.247 ± 0.226 | pior que 20 |

- 12 e 20 **empatam** estatisticamente pelo teste de Mann e Whitney (1947), com p = 0.70.
- 20 é **melhor** que 60 (p ≈ 10⁻⁷): populações grandes gastam o orçamento em poucas gerações.
- Entre as empatadas, 20 mantém mais pontos na frente final (cobre melhor a fronteira).
- **Por que ajustar o baseline é justo:** um baseline mal configurado faria o surrogate parecer
  melhor do que é. A mesma população deve ser usada nas variantes B e C.

### 2.5 Ponto de referência do HV: (1.1, 7.3)

- **Regra:** 10% pior que o pior valor de cada objetivo nas frentes **iniciais** (aleatórias)
  de 30 execuções, arredondado para cima. Pior observado: f1 = 0.990, f2 = 6.565 → **(1.1, 7.3)**.
- **Por quê:**
  - Com a referência convencional (1.1, 1.1), quase todas as soluções com 300 avaliações ficam fora
    da "cerca" e o HV fica perto de zero (0.078 em média), sem distinguir as execuções.
  - Com (1.1, 7.3), toda solução melhor que a amostragem aleatória conta.
  - A regra usa só a população inicial, que é a mesma para as três variantes (mesmas seeds),
    então não favorece nenhuma delas.
- **Cuidado:** vale só para ZDT1 com 10 variáveis. HVs só são comparáveis com a mesma referência.

### 2.6 Repetições: 10 seeds

O PDF diz que o POC I terá "poucas repetições, apenas para validar que o pipeline converge".
O estudo estatístico completo fica para o POC II.

### Parâmetros fixos do algoritmo (não são decisão nova)

Probabilidade de cruzamento **0.9**, mutação **1/n** por variável, **eta_c = eta_m = 20**:
valores do artigo original do NSGA-II (DEB et al., 2002a).

---

## 3. Resultados

### 3.1 A implementação está correta?

Testes com a configuração do artigo original do NSGA-II (DEB et al., 2002a): ZDT1 com 30 variáveis,
como em Zitzler, Deb e Thiele (2000), população 100 e 25.000 avaliações. É o cenário em que se sabe
como um NSGA-II correto se comporta.

| Teste | Resultado | Evidência |
|---|---|---|
| **T1** A frente cobre a fronteira verdadeira | ✅ Passou | IGD 0.0050; HV 0.869 (99,1% do máximo) — `T1_convergencia_zdt1.png` |
| **T2** O HV cresce ao longo das gerações | ✅ Passou | HV de 0 a 0.869; maior queda 0.0005 (ver seção 5) — `T2_curva_hv_zdt1.png` |
| **T3** O orçamento é respeitado | ✅ Passou | Nunca passa do limite; avaliação extra é bloqueada |
| **T4** Reprodutibilidade | ✅ Passou | Mesma seed → resultado idêntico |
| **T5** Outras funções ZDT | ✅ Visual | IGD entre 0.005 e 0.008 no ZDT1, 2, 3, 4 e 6 — `T5_todas_zdt.png` |
| **Comparação com o pymoo** | ✅ Coerente | Ver tabela abaixo |

**Comparação com o pymoo** (BLANK; DEB, 2020), outra biblioteca, com a mesma configuração,
10 seeds e as mesmas métricas:

| | IGD | HV |
|---|---|---|
| Nosso (DEAP) | 0.00496 ± 0.00021 | 0.8693 |
| pymoo | 0.00479 ± 0.00008 | 0.8696 |

Mesma ordem de grandeza e HV praticamente igual. O pymoo fica 3,5% melhor no IGD, uma diferença
pequena mas estatisticamente detectável (teste de Mann-Whitney, p = 0.03), atribuível a detalhes de
implementação (o pymoo elimina duplicatas antes de avaliar, por exemplo). Não afeta o POC,
porque as três variantes usam a mesma implementação.

### 3.2 O baseline no protocolo do POC I

ZDT1 com 10 variáveis, 300 avaliações, população 20, 10 seeds (`T6_cenario_caro_zdt1.png`):

| Métrica | Resultado |
|---|---|
| IGD final | **0.739 ± 0.193** |
| HV final (ref 1.1, 7.3) | **6.507 ± 0.177** |

**O que significa "longe da fronteira verdadeira".** Com só 300 avaliações, as frentes ficam
acima da curva f2 = 1 − √f1, ou seja, com valores piores que o ótimo. Exemplo de um ponto típico
do gráfico: f1 = 0.4 e f2 ≈ 1.5. Na fronteira verdadeira, com o mesmo f1 = 0.4, o melhor f2 possível
é 1 − √0.4 ≈ 0.37, então a solução encontrada é cerca de 4 vezes pior no segundo objetivo.
O IGD resume essa distância: 0.74 com 300 avaliações, contra 0.005 com 25.000 (teste T1).

A causa, dentro do ZDT1: as variáveis x₂ a x₁₀ controlam a distância à fronteira
(g = 1 + 9 × média de x₂ a x₁₀, e na fronteira g = 1). No ponto do exemplo, g ≈ 2.5, isto é,
a média dessas variáveis ainda está em torno de 0.17 em vez de 0. Em 14 gerações o algoritmo
não teve tentativas suficientes para levá-las a zero.

**Esse é o problema que este POC quer resolver.** Com um orçamento pequeno, o NSGA-II puro gasta
as avaliações em filhos gerados às cegas e termina longe do ótimo. A pergunta da Fase 3 é: se o
Random Forest escolher quais filhos merecem avaliação, as frentes terminam mais perto da curva com
as mesmas 300 avaliações? Se sim, o IGD da variante com surrogate vai ficar abaixo de 0.74.

**Esses são os números que a variante com surrogate (Fase 3) precisa superar.**

---

## 4. Como o código está organizado

### Arquivos

| Arquivo | Tipo | O que tem |
|---|---|---|
| `protocolo.py` | configuração | **Os valores das decisões da seção 2** — o único lugar para mudá-los |
| `problemas.py` | módulo | Funções ZDT, limites das variáveis e fronteira verdadeira |
| `metricas.py` | módulo | Hipervolume e IGD |
| `nsga2_baseline.py` | módulo + script | O NSGA-II, com contador de orçamento e registro por geração |
| `testes_sanidade.py` | script | Testes da seção 3.1 e gráficos |
| `experimento_decisoes.py` | script | Ponto de referência e comparação de populações |
| `comparacao_pymoo.py` | script (opcional) | Comparação com o pymoo |
| `resultados/` | saídas | Gráficos `.png` e relatórios `.txt` (recriados a cada execução) |

Os **módulos** não se rodam sozinhos: são importados pelos scripts.

```
protocolo.py ─┐
problemas.py ─┼──► nsga2_baseline.py ──► testes_sanidade.py
metricas.py ──┘                     ├──► experimento_decisoes.py
                                    └──► comparacao_pymoo.py
```

### Onde cada passo do NSGA-II está (função `rodar_nsga2`)

| Passo | Código |
|---|---|
| 1. População inicial aleatória, avaliada | `pop = tb.populacao(...)` + laço com `tb.evaluate` |
| 2. Rank e crowding da população inicial | `pop = tb.select(pop, len(pop))` |
| 3. Seleção de pais por torneio | `tools.selTournamentDCD(pop, len(pop))` |
| 4. Cruzamento SBX e mutação polinomial | `tb.mate(...)`, `tb.mutate(...)` |
| 5. Avaliação real dos filhos | `ind.fitness.values = tb.evaluate(ind)` |
| 6. Sobrevivência: pais + filhos → N melhores | `pop = tb.select(pop + filhos, tam_pop)` |
| 7. Parada pelo orçamento | `while avaliar.restante >= tam_pop` |

**Onde a Fase 3 vai mexer:** só entre os passos 4 e 5. O surrogate entra entre gerar os filhos
e avaliá-los. O resto fica igual.

---

## 5. Detalhes para saber explicar

- **O contador de avaliações** (`ContadorAvaliacoes`) embrulha a função ZDT: conta cada chamada,
  bloqueia qualquer avaliação além do orçamento e guarda cada par (x, f(x)) no **arquivo**
  (`arquivo_X`, `arquivo_F`). Na Fase 3, esse arquivo é o conjunto de treino do Random Forest.
- **`del f1.fitness.values`**: o filho nasce como cópia do pai, com a nota do pai. Depois de
  modificado, essa nota não vale mais e precisa ser apagada para forçar uma avaliação nova.
- **`pop + filhos`** é o elitismo: pais competem com filhos, então uma solução boa nunca se perde.
- **Por que o HV às vezes cai um pouquinho (T2):** o elitismo não deixa a população piorar em
  dominância, mas quando há mais pontos não dominados que vagas, o crowding distance descarta
  alguns para manter a diversidade, e a área coberta pode diminuir levemente.
- **Filhos idênticos aos pais** (sem cruzamento e sem mutação efetiva) são avaliados de novo e
  gastam orçamento. É o comportamento padrão do DEAP; não altera a comparação, desde que todas
  as variantes façam igual.
- **Seeds:** mesma seed → mesma execução, até a última casa decimal. Isso garante a
  reprodutibilidade.

---

## 6. Referências

Formato ABNT (NBR 6023). Nas citações do texto: autor em maiúsculas dentro dos parênteses,
por exemplo (DEB et al., 2002a), ou nome e ano fora deles, por exemplo Li et al. (2023).
Quando o mesmo autor tem duas obras no mesmo ano, elas se distinguem por letra (2002a, 2002b).

> **Antes de copiar para o relatório:** confira cada referência na fonte original
> (título, volume, páginas). Li et al. (2023), Chugh et al. (2018) e Knowles (2006) foram
> verificados nas páginas das editoras; os demais são referências clássicas da área.

BLANK, J.; DEB, K. pymoo: multi-objective optimization in Python. **IEEE Access**, v. 8,
p. 89497-89509, 2020. DOI: 10.1109/ACCESS.2020.2990567.

CHUGH, T.; JIN, Y.; MIETTINEN, K.; HAKANEN, J.; SINDHYA, K. A surrogate-assisted reference vector
guided evolutionary algorithm for computationally expensive many-objective optimization.
**IEEE Transactions on Evolutionary Computation**, v. 22, n. 1, p. 129-142, 2018.
DOI: 10.1109/TEVC.2016.2622301.

DEB, K.; PRATAP, A.; AGARWAL, S.; MEYARIVAN, T. A fast and elitist multiobjective genetic
algorithm: NSGA-II. **IEEE Transactions on Evolutionary Computation**, v. 6, n. 2, p. 182-197,
2002a. DOI: 10.1109/4235.996017. *(já está na proposta)*

DEB, K.; THIELE, L.; LAUMANNS, M.; ZITZLER, E. Scalable multi-objective optimization test problems.
In: CONGRESS ON EVOLUTIONARY COMPUTATION, 2002, Honolulu. **Proceedings** [...]. Piscataway: IEEE,
2002b. v. 1, p. 825-830. DOI: 10.1109/CEC.2002.1007032.

FORTIN, F.-A.; DE RAINVILLE, F.-M.; GARDNER, M.-A.; PARIZEAU, M.; GAGNÉ, C. DEAP: evolutionary
algorithms made easy. **Journal of Machine Learning Research**, v. 13, p. 2171-2175, 2012.
*(já está na proposta)*

KNOWLES, J. ParEGO: a hybrid algorithm with on-line landscape approximation for expensive
multiobjective optimization problems. **IEEE Transactions on Evolutionary Computation**, v. 10,
n. 1, p. 50-66, 2006. DOI: 10.1109/TEVC.2005.851274.

LI, F.; YANG, Y.; SHANG, Z.; LI, S.; OUYANG, H. Kriging-assisted indicator-based evolutionary
algorithm for expensive multi-objective optimization. **Applied Soft Computing**, v. 147,
art. 110736, 2023. DOI: 10.1016/j.asoc.2023.110736.

MANN, H. B.; WHITNEY, D. R. On a test of whether one of two random variables is stochastically
larger than the other. **The Annals of Mathematical Statistics**, v. 18, n. 1, p. 50-60, 1947.

ZITZLER, E.; DEB, K.; THIELE, L. Comparison of multiobjective evolutionary algorithms: empirical
results. **Evolutionary Computation**, v. 8, n. 2, p. 173-195, 2000.
DOI: 10.1162/106365600568202. *(já está na proposta)*
