"""
Microbenchmark de memória: ALOCAR -> ESCREVER -> LER -> LIBERAR

Requisitos fixos (Ficha de pré-registro, seção 4):
  - Blocos de 100 a 1000 MB, de 100 em 100
  - 100 repetições para cada tamanho
  - Tempos em milissegundos
  - Saída em CSV
  - Mesmo código no Windows e no Linux (só biblioteca padrão do Python)

Como cada operação é feita:
  - Alocação: mmap anônimo. É como o Windows (VirtualAlloc) e o Linux (mmap)
    entregam blocos grandes de memória para um processo.
  - Escrita:  memset grava o valor 0xAB em todos os bytes do bloco.
  - Leitura:  percorre o bloco inteiro procurando um byte 0x00. Como tudo
    foi escrito com 0xAB, nada é encontrado: isso também confirma a escrita.
  - Liberação: fecha o mmap e devolve a memória ao sistema.

Uso:
  Windows:  python benchmark.py
  Linux:    python3 benchmark.py

  Teste-piloto (rápido, só para conferir se funciona):
            python3 benchmark.py --piloto

  Esperar antes de começar (intervalo de estabilização, em segundos):
            python3 benchmark.py --espera 120

Saída:
  dados/resultados_<sistema>.csv   (coleta definitiva)
  dados/piloto_<sistema>.csv       (teste-piloto)
"""

import argparse
import csv
import ctypes
import gc
import mmap
import os
import platform
import sys
import time

MB = 1024 * 1024
BLOCOS_MB = list(range(100, 1001, 100))  # 100, 200, ..., 1000
REPETICOES = 100
VALOR = 0xAB

CABECALHO = ["sistema", "bloco_MB", "teste", "alloc_ms", "write_ms", "read_ms", "free_ms"]


def ns_para_ms(ns):
    return round(ns / 1_000_000, 4)


def um_teste(tamanho):
    """Executa alocar -> escrever -> ler -> liberar e devolve os 4 tempos em ms."""
    # 1) Alocação
    t0 = time.perf_counter_ns()
    bloco = mmap.mmap(-1, tamanho)
    t1 = time.perf_counter_ns()

    # 2) Escrita
    visao = (ctypes.c_char * tamanho).from_buffer(bloco)
    ctypes.memset(visao, VALOR, tamanho)
    del visao
    t2 = time.perf_counter_ns()

    # 3) Leitura
    posicao = bloco.find(b"\x00")
    t3 = time.perf_counter_ns()
    if posicao != -1:
        raise RuntimeError(f"Erro de verificação: byte não escrito na posição {posicao}")

    # 4) Liberação
    bloco.close()
    t4 = time.perf_counter_ns()

    return (
        ns_para_ms(t1 - t0),
        ns_para_ms(t2 - t1),
        ns_para_ms(t3 - t2),
        ns_para_ms(t4 - t3),
    )


def main():
    parser = argparse.ArgumentParser(description="Microbenchmark de memória")
    parser.add_argument("--piloto", action="store_true",
                        help="teste rápido: blocos de 100 e 200 MB, 3 repetições")
    parser.add_argument("--espera", type=int, default=0,
                        help="segundos de espera antes de começar (estabilização)")
    args = parser.parse_args()

    sistema = platform.system().lower()  # "windows" ou "linux"
    if sistema not in ("windows", "linux"):
        sys.exit(f"Sistema não suportado: {sistema}")

    if args.piloto:
        blocos, repeticoes, prefixo = [100, 200], 3, "piloto"
    else:
        blocos, repeticoes, prefixo = BLOCOS_MB, REPETICOES, "resultados"

    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
    os.makedirs(pasta, exist_ok=True)
    arquivo = os.path.join(pasta, f"{prefixo}_{sistema}.csv")

    if os.path.exists(arquivo) and not args.piloto:
        sys.exit(f"O arquivo {arquivo} já existe. Renomeie ou apague antes de rodar de novo.")

    total = len(blocos) * repeticoes
    print(f"Sistema: {sistema} | Python {platform.python_version()}")
    print(f"Blocos: {blocos[0]} a {blocos[-1]} MB | {repeticoes} repetições | {total} testes")
    print(f"Saída: {arquivo}")

    if args.espera > 0:
        print(f"Aguardando {args.espera} s de estabilização...")
        time.sleep(args.espera)

    gc.disable()  # evita que o coletor de lixo do Python interfira nas medições
    inicio = time.time()
    feitos = 0

    with open(arquivo, "w", newline="", encoding="utf-8") as f:
        escritor = csv.writer(f)
        escritor.writerow(CABECALHO)

        for bloco_mb in blocos:
            tamanho = bloco_mb * MB
            for teste in range(1, repeticoes + 1):
                alloc_ms, write_ms, read_ms, free_ms = um_teste(tamanho)
                escritor.writerow([sistema, bloco_mb, teste,
                                   alloc_ms, write_ms, read_ms, free_ms])
                feitos += 1
            f.flush()  # garante que o que já foi medido fica salvo
            decorrido = time.time() - inicio
            print(f"  {bloco_mb:>4} MB concluído | {feitos}/{total} testes | {decorrido:.0f} s")

    gc.enable()
    print(f"\nFim. {feitos} registros salvos em {arquivo}")


if __name__ == "__main__":
    main()
