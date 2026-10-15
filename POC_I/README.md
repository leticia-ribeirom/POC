# POC I — Algoritmos evolutivos multiobjetivo mais eficientes com modelo substituto e LLM

Leticia Ribeiro Miranda · Orientadora: Profa. Gisele Lobo Pappa · UFMG

O projeto compara três variantes sob um orçamento curto de avaliações reais:
**A** = NSGA-II puro (baseline), **B** = NSGA-II + surrogate (Random Forest) e
**C** = NSGA-II + surrogate + LLM (API do Claude).

Na reunião de 13/10/2026, a orientadora sugeriu trocar o benchmark pela suíte **`bbob-biobj`** da
plataforma COCO e usar os **indicadores do próprio COCO**. O projeto recomeçou a partir daí:
**todos os testes, gráficos e decisões foram feitos no `bbob-biobj`.**

## Estrutura

```
POC/
└── POC_I/
    ├── README.md          ← este arquivo (visão geral)
    ├── 1. baseline/       ← o NSGA-II (variante A) rodando no bbob-biobj
    ├── 2. benchmark/      ← o benchmark (bbob-biobj + COCO), usado por todas as variantes
    └── documentos/        ← documento de decisões para a orientadora e a figura do funil
```

| Pasta | O que tem | Principais resultados |
|---|---|---|
| **`1. baseline/`** | O NSGA-II em DEAP, os testes de correção, o experimento completo (2.475 execuções) e os experimentos de decisão (população e amostra inicial) | delta_HV mediano 0,27 / 0,29 / 0,31 (D = 5 / 10 / 20); melhor que a busca aleatória em 78% / 97% / 100% das execuções; população 20 |
| **`2. benchmark/`** | A suíte `bbob-biobj` (55 funções de 2 objetivos, 15 grupos), o protocolo (D = 5, 10, 20; instâncias 1 a 15; orçamento 30 × D), os indicadores do COCO e a busca aleatória (o piso) | 4/4 testes do benchmark passam |
| **`documentos/`** | `decisoes_projeto_POC_I.docx` e `figuras/F1_funil_metodo.png` (uma geração do método) | — |

Cada pasta tem o próprio `README.md`, com passo a passo, decisões e referências. O benchmark
explica o problema e como a qualidade é medida; o baseline é o algoritmo rodando nele. Os
scripts do baseline buscam o benchmark na pasta vizinha, então as duas precisam ficar lado a lado
dentro de `POC_I`.

## Como rodar

No VS Code, abra a pasta **`POC_I`** (**File → Open Folder**) e, no terminal
(**Terminal → New Terminal**):

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (Mac/Linux: source .venv/bin/activate)
pip install deap numpy scipy matplotlib moocore coco-experiment cocopp cairosvg

cd "2. benchmark"
python testes_benchmark.py         # confere o benchmark (~10 s)

cd "../1. baseline"
python testes_baseline.py          # testes de correção do NSGA-II (~1 min)
python experimento_baseline.py     # baseline completo + análise do COCO (~5 min)
python experimento_populacao.py    # decisão da população (~10 min)
python grafico_populacao.py
python experimento_amostra_inicial.py   # decisão da amostra inicial (~6 min)
python grafico_amostra_inicial.py
```

As aspas em `cd "1. baseline"` são necessárias por causa do espaço no nome. Rode pelo terminal,
de dentro da pasta, e não pelo botão ▶ do VS Code (ele rodaria a partir de `POC_I`, e os
resultados iriam para o lugar errado). As pastas `exdata/` e `ppdata/` (dados brutos e análise do
COCO) não vão no zip nem no git; elas são recriadas quando você roda os experimentos.

## Plano do POC I

| Fase | O que fazer | Situação |
|---|---|---|
| 1. Baseline | NSGA-II validado e rodado no benchmark; população e amostra inicial testadas (`1. baseline/`) | ✅ |
| 2. Benchmark | `bbob-biobj`, protocolo e indicadores do COCO (`2. benchmark/`) | ✅ |
| 3. Surrogate | Random Forest com pré-seleção (100, 200 ou 500 candidatos → 20 avaliados) | próxima |
| 4. A × B | experimento completo + análise do COCO | a fazer |
| 5. LLM | API do Claude; primeiro com um "LLM falso" para testar o encaixe | a fazer |
| 6. A × B × C | comparação final, ECDF, estatística e custo | a fazer |
| Entregas | relatório (artigo IEEE), vídeo pitch, pôster | ao longo do semestre |

**Em aberto (para conversar com a orientadora):** orçamento 30 × D; população por dimensão ou 20
em todas; tamanho da amostra inicial (20, 40 ou 11D − 1); regra de pré-seleção e retreino do
Random Forest; número de candidatos (100, 200 ou 500); se o LLM roda nas 55 funções ou num
subconjunto, por causa do custo da API.

O histórico de todas as mudanças está no git (`git log`), inclusive a versão anterior com o ZDT1.
