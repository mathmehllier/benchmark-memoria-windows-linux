"""
Valida os arquivos CSV conforme as regras da Ficha de pré-registro (seção 10).

Uso:
  python validar_csv.py                          (valida todos os dados/resultados_*.csv)
  python validar_csv.py dados/resultados_linux.csv
"""

import csv
import glob
import os
import sys

COLUNAS = ["sistema", "bloco_MB", "teste", "alloc_ms", "write_ms", "read_ms", "free_ms"]
TEMPOS = ["alloc_ms", "write_ms", "read_ms", "free_ms"]
BLOCOS_ESPERADOS = set(range(100, 1001, 100))
TESTES_ESPERADOS = set(range(1, 101))
TOTAL_ESPERADO = len(BLOCOS_ESPERADOS) * len(TESTES_ESPERADOS)  # 1000


def validar(caminho):
    nome = os.path.basename(caminho).lower()
    sistema_esperado = "windows" if "windows" in nome else "linux" if "linux" in nome else None

    erros = {regra: [] for regra in [
        "Colunas", "Quantidade de registros", "Tamanhos dos blocos", "Número dos testes",
        "Duplicidades", "Valores ausentes", "Tipos", "Tempos não negativos", "Identificação",
    ]}

    with open(caminho, newline="", encoding="utf-8") as f:
        leitor = csv.DictReader(f)
        if leitor.fieldnames != COLUNAS:
            erros["Colunas"].append(f"esperado {COLUNAS}, encontrado {leitor.fieldnames}")
        linhas = list(leitor)

    vistos = set()
    testes_por_bloco = {}

    for n, linha in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        # Valores ausentes
        vazias = [c for c in COLUNAS if not (linha.get(c) or "").strip()]
        if vazias:
            erros["Valores ausentes"].append(f"linha {n}: {vazias}")
            continue

        # Tipos
        try:
            bloco = int(linha["bloco_MB"])
            teste = int(linha["teste"])
            tempos = {c: float(linha[c]) for c in TEMPOS}
        except ValueError:
            erros["Tipos"].append(f"linha {n}")
            continue

        # Identificação
        sistema = linha["sistema"].strip().lower()
        if sistema not in ("windows", "linux") or (sistema_esperado and sistema != sistema_esperado):
            erros["Identificação"].append(f"linha {n}: '{linha['sistema']}'")

        # Blocos e testes
        if bloco not in BLOCOS_ESPERADOS:
            erros["Tamanhos dos blocos"].append(f"linha {n}: {bloco}")
        if teste not in TESTES_ESPERADOS:
            erros["Número dos testes"].append(f"linha {n}: {teste}")
        testes_por_bloco.setdefault(bloco, set()).add(teste)

        # Tempos
        negativos = [c for c, v in tempos.items() if v < 0]
        if negativos:
            erros["Tempos não negativos"].append(f"linha {n}: {negativos}")

        # Duplicidades (sistema + bloco + teste)
        chave = (sistema, bloco, teste)
        if chave in vistos:
            erros["Duplicidades"].append(f"linha {n}: {chave}")
        vistos.add(chave)

    if len(linhas) != TOTAL_ESPERADO:
        erros["Quantidade de registros"].append(f"esperado {TOTAL_ESPERADO}, encontrado {len(linhas)}")

    faltando = BLOCOS_ESPERADOS - set(testes_por_bloco)
    if faltando:
        erros["Tamanhos dos blocos"].append(f"blocos ausentes: {sorted(faltando)}")
    for bloco, testes in sorted(testes_por_bloco.items()):
        if bloco in BLOCOS_ESPERADOS and testes != TESTES_ESPERADOS:
            erros["Número dos testes"].append(f"bloco {bloco}: faltam {sorted(TESTES_ESPERADOS - testes)[:5]}...")

    print(f"\n{caminho}")
    print("-" * 60)
    ok_geral = True
    for regra, lista in erros.items():
        if lista:
            ok_geral = False
            print(f"  [ERRO] {regra}: {len(lista)} problema(s)")
            for item in lista[:5]:
                print(f"         - {item}")
        else:
            print(f"  [OK]   {regra}")
    print("  RESULTADO:", "VÁLIDO" if ok_geral else "INVÁLIDO")
    return ok_geral


def main():
    arquivos = sys.argv[1:] or sorted(glob.glob(os.path.join("dados", "resultados_*.csv")))
    if not arquivos:
        sys.exit("Nenhum arquivo encontrado. Informe o caminho do CSV.")
    resultados = [validar(a) for a in arquivos]
    sys.exit(0 if all(resultados) else 1)


if __name__ == "__main__":
    main()
