"""
rodar_tudo.py — Roda o benchmark e o baseline inteiros, na ordem certa.

Rode de dentro da pasta POC_I:

    python rodar_tudo.py            tudo (~25 min): testes, baseline, população, amostra inicial
    python rodar_tudo.py --rapido   só os testes e a demonstração (~1 min)
    python rodar_tudo.py --lista    mostra as etapas sem rodar nada

Funciona no Windows, no Mac e no Linux: cada script é chamado com o mesmo Python
que está rodando este arquivo (o do .venv, se ele estiver ativo) e de dentro da
própria pasta, para os resultados irem para o lugar certo. Se uma etapa falhar,
o script para e mostra qual foi.
"""

import os
import subprocess
import sys
import time

RAIZ = os.path.dirname(os.path.abspath(__file__))


def achar_pasta(arquivo_marca):
    """Acha a pasta (dentro de POC_I) que contém `arquivo_marca`, qualquer que seja o nome."""
    for nome in sorted(os.listdir(RAIZ)):
        pasta = os.path.join(RAIZ, nome)
        if os.path.isfile(os.path.join(pasta, arquivo_marca)):
            return pasta
    sys.exit(f"Não achei a pasta que contém {arquivo_marca} dentro de {RAIZ}.")


BENCHMARK = achar_pasta("testes_benchmark.py")
BASELINE = achar_pasta("testes_baseline.py")

# (pasta, script, descrição, entra no modo --rapido?)
ETAPAS = [
    (BENCHMARK, "funcoes_bbob.py", "Benchmark: lista das 55 funções", True),
    (BENCHMARK, "testes_benchmark.py", "Benchmark: testes B1 a B4", True),
    (BASELINE, "nsga2_baseline.py", "Baseline: demonstração (f1, D = 10)", True),
    (BASELINE, "testes_baseline.py", "Baseline: testes de correção T1 a T6", True),
    (BASELINE, "experimento_baseline.py", "Baseline: 2.475 execuções + análise do COCO", False),
    (BASELINE, "experimento_populacao.py", "Decisão: tamanho da população", False),
    (BASELINE, "grafico_populacao.py", "Gráfico P1 (população)", False),
    (BASELINE, "experimento_amostra_inicial.py", "Decisão: amostra inicial", False),
    (BASELINE, "grafico_amostra_inicial.py", "Gráfico A1 (amostra inicial)", False),
]


def main():
    rapido = "--rapido" in sys.argv
    etapas = [e for e in ETAPAS if e[3] or not rapido]

    if "--lista" in sys.argv:
        for i, (pasta, script, desc, _) in enumerate(etapas, 1):
            print(f"{i}. {desc}  ({os.path.basename(pasta)}/{script})")
        return

    print(f"Python: {sys.executable}")
    print(f"{len(etapas)} etapas{' (modo rápido)' if rapido else ''}\n")
    inicio = time.perf_counter()
    for i, (pasta, script, desc, _) in enumerate(etapas, 1):
        print("=" * 70)
        print(f"[{i}/{len(etapas)}] {desc}")
        print(f"      {os.path.basename(pasta)}/{script}")
        print("=" * 70, flush=True)
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, script], cwd=pasta)
        if r.returncode != 0:
            sys.exit(f"\nA etapa {i} ({os.path.basename(pasta)}/{script}) falhou. "
                     "Corrija o erro acima e rode de novo.")
        print(f"\n      ok em {time.perf_counter() - t0:.0f} s\n", flush=True)

    total = time.perf_counter() - inicio
    print("=" * 70)
    print(f"Tudo pronto em {total / 60:.1f} min.")
    print(f"Resultados: {os.path.basename(BENCHMARK)}/resultados e {os.path.basename(BASELINE)}/resultados")
    if not rapido:
        print(f"Análise do COCO: abra {os.path.basename(BASELINE)}/ppdata/index.html no navegador")


if __name__ == "__main__":
    main()
