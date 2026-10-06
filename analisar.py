"""
Análise comparativa Windows x Linux (Ficha de pré-registro, seção 11).

Plano de análise:
  - Os registros são agrupados por sistema, tamanho do bloco e operação.
  - Para cada grupo: média, mediana, desvio padrão, mínimo e máximo.
  - Resultados apresentados em tabelas (CSV) e gráficos de linha.
  - Um sistema tem melhor desempenho em uma operação quando sua MEDIANA de
    tempo é menor (a mediana é menos sensível a valores atípicos).
  - Se o vencedor mudar entre operações ou tamanhos, a recomendação considera
    o tempo total do ciclo (alocar + escrever + ler + liberar).

Uso:
  pip install -r requirements.txt
  python analisar.py

Saídas:
  resultados/estatisticas.csv   estatísticas por sistema, bloco e operação
  resultados/comparacao.csv     medianas lado a lado, diferença % e vencedor
  graficos/medianas_por_operacao.png
  graficos/diferenca_percentual.png
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PASTA = os.path.dirname(os.path.abspath(__file__))
OPERACOES = {"alloc_ms": "Alocação", "write_ms": "Escrita",
             "read_ms": "Leitura", "free_ms": "Liberação"}
CORES = {"linux": "#2a78d6", "windows": "#eb6834"}
MARCADORES = {"linux": "o", "windows": "s"}
NOMES = {"linux": "Linux", "windows": "Windows"}
TEXTO = "#3d3d3a"
GRADE = "#e6e5df"


def carregar():
    arquivos = [os.path.join(PASTA, "dados", f"resultados_{s}.csv") for s in ("linux", "windows")]
    faltando = [a for a in arquivos if not os.path.exists(a)]
    if faltando:
        raise SystemExit(f"Arquivo(s) não encontrado(s): {faltando}")
    dados = pd.concat([pd.read_csv(a) for a in arquivos], ignore_index=True)
    dados["total_ms"] = dados[list(OPERACOES)].sum(axis=1)
    # formato longo: uma linha por sistema, bloco, teste e operação
    return dados.melt(id_vars=["sistema", "bloco_MB", "teste"],
                      value_vars=list(OPERACOES) + ["total_ms"],
                      var_name="operacao", value_name="tempo_ms")


def estatisticas(longo):
    est = (longo.groupby(["operacao", "bloco_MB", "sistema"])["tempo_ms"]
           .agg(media="mean", mediana="median", desvio_padrao="std", minimo="min", maximo="max",
                q1=lambda x: x.quantile(0.25), q3=lambda x: x.quantile(0.75))
           .reset_index())
    return est


def comparacao(est):
    tab = est.pivot_table(index=["operacao", "bloco_MB"], columns="sistema", values="mediana").reset_index()
    tab.columns.name = None
    tab = tab.rename(columns={"linux": "mediana_linux_ms", "windows": "mediana_windows_ms"})
    tab["dif_windows_vs_linux_pct"] = (
        (tab["mediana_windows_ms"] - tab["mediana_linux_ms"]) / tab["mediana_linux_ms"] * 100)
    tab["mais_rapido"] = tab.apply(
        lambda r: "Linux" if r["mediana_linux_ms"] < r["mediana_windows_ms"] else "Windows", axis=1)
    return tab


def estilo(ax, titulo):
    ax.set_title(titulo, loc="left", fontsize=11, color=TEXTO, fontweight="bold")
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    for lado in ("left", "bottom"):
        ax.spines[lado].set_color("#b8b7ae")
    ax.tick_params(colors=TEXTO, labelsize=9)


def grafico_medianas(est, destino):
    fig, eixos = plt.subplots(2, 2, figsize=(11, 7.5))
    for ax, (op, nome) in zip(eixos.flat, OPERACOES.items()):
        parte = est[est["operacao"] == op]
        for sistema in ("linux", "windows"):
            s = parte[parte["sistema"] == sistema].sort_values("bloco_MB")
            ax.fill_between(s["bloco_MB"], s["q1"], s["q3"], color=CORES[sistema], alpha=0.15, linewidth=0)
            ax.plot(s["bloco_MB"], s["mediana"], color=CORES[sistema], linewidth=2,
                    marker=MARCADORES[sistema], markersize=5, label=NOMES[sistema])
        estilo(ax, nome)
        ax.set_xticks(range(100, 1001, 100))
        ax.set_xlabel("Tamanho do bloco (MB)", color=TEXTO, fontsize=9)
        ax.set_ylabel("Mediana do tempo (ms)", color=TEXTO, fontsize=9)
        ax.set_ylim(bottom=0)
    eixos.flat[0].legend(frameon=False, fontsize=9)
    fig.suptitle("Mediana do tempo por operação (faixa = 1º ao 3º quartil, 100 repetições)",
                 x=0.01, ha="left", fontsize=12, color=TEXTO)
    fig.tight_layout()
    fig.savefig(destino, dpi=150)
    plt.close(fig)


def grafico_diferenca(comp, destino):
    fig, ax = plt.subplots(figsize=(10, 5))
    cores = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#3d3d3a"]
    marcas = ["o", "s", "^", "D", "x"]
    nomes = {**OPERACOES, "total_ms": "Ciclo completo"}
    for (op, nome), cor, m in zip(nomes.items(), cores, marcas):
        s = comp[comp["operacao"] == op].sort_values("bloco_MB")
        ax.plot(s["bloco_MB"], s["dif_windows_vs_linux_pct"], color=cor, marker=m,
                markersize=5, linewidth=2, label=nome)
    ax.axhline(0, color="#8a897f", linewidth=1)
    estilo(ax, "Diferença das medianas: Windows em relação ao Linux (%)")
    ax.set_xticks(range(100, 1001, 100))
    ax.set_xlabel("Tamanho do bloco (MB)", color=TEXTO, fontsize=9)
    ax.set_ylabel("Diferença (%)  — acima de 0: Windows mais lento", color=TEXTO, fontsize=9)
    ax.legend(frameon=False, fontsize=9, ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    fig.tight_layout()
    fig.savefig(destino, dpi=150)
    plt.close(fig)


def main():
    longo = carregar()
    est = estatisticas(longo)
    comp = comparacao(est)

    os.makedirs(os.path.join(PASTA, "resultados"), exist_ok=True)
    os.makedirs(os.path.join(PASTA, "graficos"), exist_ok=True)
    est.round(4).to_csv(os.path.join(PASTA, "resultados", "estatisticas.csv"), index=False)
    comp.round(4).to_csv(os.path.join(PASTA, "resultados", "comparacao.csv"), index=False)
    grafico_medianas(est, os.path.join(PASTA, "graficos", "medianas_por_operacao.png"))
    grafico_diferenca(comp, os.path.join(PASTA, "graficos", "diferenca_percentual.png"))

    # Resumo no terminal
    nomes = {**OPERACOES, "total_ms": "Ciclo completo"}
    print("\nMEDIANAS (ms) — bloco de 1000 MB")
    b = comp[comp["bloco_MB"] == 1000].set_index("operacao").loc[list(nomes)]
    for op, r in b.iterrows():
        print(f"  {nomes[op]:<15} Linux {r['mediana_linux_ms']:>10.3f} | Windows {r['mediana_windows_ms']:>10.3f}"
              f" | dif {r['dif_windows_vs_linux_pct']:>+8.1f}% | mais rápido: {r['mais_rapido']}")

    print("\nVITÓRIAS POR OPERAÇÃO (em 10 tamanhos de bloco)")
    for op in nomes:
        v = comp[comp["operacao"] == op]["mais_rapido"].value_counts()
        print(f"  {nomes[op]:<15} Linux {v.get('Linux', 0):>2} | Windows {v.get('Windows', 0):>2}")

    total = longo[longo["operacao"] == "total_ms"].groupby("sistema")["tempo_ms"].sum() / 1000
    print("\nTEMPO TOTAL DE TODOS OS CICLOS (s)")
    for s, v in total.items():
        print(f"  {NOMES[s]:<8} {v:.1f} s")
    print("\nArquivos gerados em resultados/ e graficos/")


if __name__ == "__main__":
    main()
