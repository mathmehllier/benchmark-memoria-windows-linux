# Windows ou Linux? Microbenchmark de memória

Trabalho da disciplina **Programação para Ciência de Dados** (UNIJUÍ).

**Pergunta norteadora:** em condições experimentais equivalentes, qual sistema operacional apresenta melhor desempenho nas operações de alocação, escrita, leitura e liberação de memória?

## Estrutura

```
benchmark.py          # microbenchmark: alocar -> escrever -> ler -> liberar
validar_csv.py        # confere os CSV com as regras da ficha (seção 10)
coletar_ambiente.py   # registra a configuração de cada ambiente
dados/                # CSV gerados (resultados_linux.csv, resultados_windows.csv)
ambientes/            # ambiente_linux.txt, ambiente_windows.txt
```

## Configuração experimental

Duas máquinas virtuais no VirtualBox, no mesmo computador, uma ligada por vez.

| Item | Valor |
|---|---|
| Hardware físico | Intel Core i5-8300H (4 núcleos / 8 lógicos), 8 GB RAM |
| Sistema hospedeiro | Windows 10 |
| VM Linux | Ubuntu 26.04 — 4096 MB RAM, 2 vCPUs, disco 64 GB |
| VM Windows | Windows 11 — 4096 MB RAM, 2 vCPUs, disco 64 GB |

Detalhes completos em `ambientes/`.

## Parâmetros (fixos)

- Blocos de 100 a 1000 MB, de 100 em 100
- 100 repetições por bloco (1000 registros por sistema)
- Tempos em milissegundos, salvos em CSV
- Mesmo código e mesma versão do Python nos dois sistemas
- Só biblioteca padrão do Python (nada para instalar)

## Como reproduzir

Em cada sistema, um de cada vez, com os demais programas fechados:

```bash
# 1. Registrar o ambiente
python3 coletar_ambiente.py          # no Windows: python

# 2. Teste-piloto (rápido)
python3 benchmark.py --piloto

# 3. Coleta definitiva, com 2 minutos de estabilização
python3 benchmark.py --espera 120

# 4. Validar o CSV
python3 validar_csv.py
```

## Formato do CSV

```
sistema,bloco_MB,teste,alloc_ms,write_ms,read_ms,free_ms
linux,100,1,0.0223,91.8139,9.5012,11.4806
```

## Como cada operação é medida

| Operação | Implementação |
|---|---|
| Alocação | `mmap` anônimo (o SO reserva o bloco) |
| Escrita | `memset` grava `0xAB` em todos os bytes |
| Leitura | percorre o bloco inteiro procurando `0x00` (também confirma a escrita) |
| Liberação | `close()` do mmap (memória devolvida ao SO) |

O coletor de lixo do Python fica desligado durante a coleta para não interferir nos tempos.
