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
    ├── rodar_tudo.py      ← roda o benchmark e o baseline inteiros, na ordem certa
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
(**Terminal → New Terminal**), crie o ambiente e instale as bibliotecas (uma vez só):

| Windows | Mac / Linux / WSL |
|---|---|
| `python -m venv .venv` | `python3 -m venv .venv` |
| `.venv\Scripts\activate` | `source .venv/bin/activate` |

```bash
pip install deap numpy scipy matplotlib moocore coco-experiment cocopp cairosvg
```

Depois, **um comando roda tudo**, na ordem certa:

```bash
python rodar_tudo.py            # tudo (~25 min): testes, baseline, população, amostra inicial
python rodar_tudo.py --rapido   # só os testes e a demonstração (~1 min)
python rodar_tudo.py --lista    # mostra as etapas sem rodar
```

| # | Etapa | Pasta | Tempo |
|---|---|---|---|
| 1 | Lista das 55 funções | `2. benchmark` | segundos |
| 2 | Testes do benchmark (B1 a B4) | `2. benchmark` | segundos |
| 3 | Demonstração do NSGA-II | `1. baseline` | < 1 s |
| 4 | Testes de correção (T1 a T6) | `1. baseline` | ~30 s |
| 5 | Baseline completo (2.475 execuções) + análise do COCO | `1. baseline` | ~5 min |
| 6–7 | Decisão da população + gráfico P1 | `1. baseline` | ~10 min |
| 8–9 | Decisão da amostra inicial + gráfico A1 | `1. baseline` | ~6 min |

O `rodar_tudo.py` chama cada script com o mesmo Python (o do `.venv`) e de dentro da pasta
certa, então funciona igual no Windows, no Mac e no Linux. Se uma etapa falhar, ele para e diz
qual foi. Também dá para rodar um script sozinho: entre na pasta (`cd "1. baseline"`, com aspas
por causa do espaço) e rode `python nome_do_script.py`.

As pastas `exdata/` e `ppdata/` (dados brutos e análise do COCO) não vão no zip nem no git; elas
são recriadas quando você roda os experimentos. A análise completa do COCO fica em
`1. baseline/ppdata/index.html`.

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
