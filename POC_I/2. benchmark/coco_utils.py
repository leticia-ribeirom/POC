"""
coco_utils.py — Ligação entre o NSGA-II e a plataforma COCO.

  - rodar_no_bbob: roda um otimizador em todos os problemas escolhidos do
    bbob-biobj, com o observador do COCO registrando cada avaliação;
  - ler_resultados_finais: lê os arquivos gravados pelo COCO e devolve o
    indicador final de cada execução.

Usado pelo baseline (../fase2_baseline) e, depois, pelas variantes B e C.

O INDICADOR DO COCO (BROCKHOFF et al., 2016)
  O COCO guarda todas as soluções não dominadas avaliadas (o arquivo), com os
  objetivos normalizados pelos pontos ideal e nadir. A qualidade é a
  DIFERENÇA entre o hipervolume de referência (o da melhor aproximação
  conhecida da fronteira) e o hipervolume do arquivo:

      delta_HV = HV_referencia - HV_arquivo        (menor é melhor; 0 = alcançou)

  Se nenhuma solução dominar o nadir, o COCO usa a distância até a região de
  interesse (o valor fica acima do HV de referência). O desempenho oficial é o
  NÚMERO DE AVALIAÇÕES até atingir cada um dos alvos de delta_HV, mostrado em
  curvas ECDF pelo cocopp.
"""

import os
import re
import shutil

import cocoex

from problemas import obter_problema_bbob


def _compactar(numeros):
    """[1,2,3,7,8] -> '1-3,7-8' (o COCO não aceita listas muito longas)."""
    numeros = sorted(set(numeros))
    partes, ini = [], numeros[0]
    for a, b in zip(numeros, numeros[1:] + [None]):
        if b != a + 1:
            partes.append(f"{ini}-{a}" if a > ini else f"{a}")
            ini = b
    return ",".join(partes)


def rodar_no_bbob(otimizador, nome_algoritmo, funcoes, dimensoes, instancias,
                  orcamento, seed, progresso=True):
    """Roda `otimizador` em cada problema (função, dimensão, instância).

    otimizador(problema_dict, orcamento, seed) -> qualquer coisa
    orcamento(dimensao) -> int
    seed(instancia) -> int

    Os dados do COCO vão para exdata/<nome_algoritmo>/, sempre a partir da
    pasta onde o script é executado: o próprio COCO acrescenta "exdata/" ao
    nome e não aceita outro caminho. A pasta é apagada antes, para não
    misturar execuções. Devolve o caminho dessa pasta.
    """
    pasta = os.path.join("exdata", nome_algoritmo)
    if os.path.exists(pasta):
        shutil.rmtree(pasta)

    filtro = ("function_indices:" + _compactar(funcoes) +
              " dimensions:" + ",".join(map(str, dimensoes)) +
              " instance_indices:" + _compactar(instancias))
    suite = cocoex.Suite("bbob-biobj", "", filtro)
    observador = cocoex.Observer(
        "bbob-biobj",
        f"result_folder: {nome_algoritmo} algorithm_name: {nome_algoritmo}")

    total = len(suite)
    for k, problema_coco in enumerate(suite, start=1):
        problema_coco.observe_with(observador)
        problema = obter_problema_bbob(problema_coco)
        otimizador(problema, orcamento(problema_coco.dimension),
                   seed(problema_coco.id_instance))
        if problema_coco.evaluations > orcamento(problema_coco.dimension):
            raise RuntimeError(f"{problema_coco.id} passou do orçamento!")
        problema_coco.free()
        if progresso and (k % 100 == 0 or k == total):
            print(f"  {k}/{total} problemas concluídos")
    return pasta


_NOME_DAT = re.compile(r"bbob-biobj_f(\d+)_d(\d+)_hyp\.dat$")


def ler_resultados_finais(pasta):
    """Lê os arquivos _hyp.dat do COCO (precisão completa). Devolve uma lista
    de dicionários com funcao, dimensao, instancia, avaliacoes e delta_hv
    (o indicador na ÚLTIMA avaliação de cada execução).

    Os .info também têm o valor final, mas arredondado para 2 algarismos;
    por isso lemos os .dat."""
    linhas = []
    for raiz, _, arquivos in os.walk(pasta):
        for nome in arquivos:
            m = _NOME_DAT.search(nome)
            if not m:
                continue
            funcao, dim = int(m.group(1)), int(m.group(2))
            inst, ultima = None, None
            with open(os.path.join(raiz, nome), encoding="utf-8") as f:
                for linha in f:
                    if linha.startswith("% instance"):
                        if inst is not None and ultima is not None:
                            linhas.append(dict(funcao=funcao, dimensao=dim, instancia=inst,
                                               avaliacoes=ultima[0], delta_hv=ultima[1]))
                        inst = int(linha.split("=")[1].split(",")[0])
                        ultima = None
                    elif not linha.startswith("%") and linha.strip():
                        partes = linha.split()
                        ultima = (int(partes[0]), float(partes[1]))
            if inst is not None and ultima is not None:
                linhas.append(dict(funcao=funcao, dimensao=dim, instancia=inst,
                                   avaliacoes=ultima[0], delta_hv=ultima[1]))
    return linhas
