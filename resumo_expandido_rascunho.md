**WINDOWS OU LINUX? ANÁLISE DO DESEMPENHO DE OPERAÇÕES DE MEMÓRIA PARA A INTEGRAÇÃO DE SERVIÇOS DIGITAIS EM CIDADES INTELIGENTES¹**

**Matheus Oliveira², Erik Luan³, Pedro Bickel⁴, Eduardo Coracini⁵**

¹ Trabalho da disciplina Programação para Ciência de Dados, desenvolvido na Unijuí.
² Estudante do curso de Ciência da Computação da Unijuí.
³ Estudante do curso de Ciência da Computação da Unijuí.
⁴ Estudante do curso de Ciência da Computação da Unijuí.
⁵ Estudante do curso de Ciência da Computação da Unijuí.

**INTRODUÇÃO**

Cidades inteligentes dependem da integração de serviços digitais oferecidos pelos setores público e privado. Essa integração é feita por processos que recebem dados de diferentes serviços, processam essas informações e as encaminham ao destino adequado. Em um atendimento de urgência, por exemplo, um processo de integração precisa combinar dados da ambulância, do hospital, da disponibilidade de leitos e das condições de trânsito para definir o hospital de destino e a rota de deslocamento. Nesse cenário, atrasos no processamento podem comprometer o atendimento e colocar a vida do paciente em risco.

Durante sua execução, esse processo realiza repetidamente operações de alocação, escrita, leitura e liberação de memória. Como o processo é executado no espaço de usuário (user space), essas operações dependem dos serviços oferecidos pelo sistema operacional, que é o software privilegiado responsável por gerenciar a memória física. Assim, a escolha do sistema operacional pode influenciar o tempo de resposta da integração.

A empresa responsável pela plataforma avalia o uso de Windows ou Linux, mas não possui evidências experimentais comparáveis sobre o desempenho dessas operações. Diante disso, este trabalho buscou responder à seguinte pergunta: em condições experimentais equivalentes, qual dos sistemas operacionais apresenta melhor desempenho nas operações de alocação, escrita, leitura e liberação de memória? A hipótese do grupo foi a de que o sistema operacional influencia o tempo dessas operações e que um dos sistemas gerencia a memória de forma mais eficiente, especialmente em blocos maiores. O tema se relaciona ao Objetivo de Desenvolvimento Sustentável 11 (Cidades e Comunidades Sustentáveis) da Agenda 2030 da ONU, ao tratar da infraestrutura tecnológica de serviços urbanos críticos.

**METODOLOGIA**

Foi desenvolvido um microbenchmark em Python que executa, para cada repetição, a sequência alocar, escrever, ler e liberar um bloco de memória. Os blocos variaram de 100 a 1.000 MB, com incremento de 100 MB, e cada tamanho foi repetido 100 vezes, totalizando 1.000 registros por sistema. Os tempos foram medidos em milissegundos com o relógio de alta resolução do Python (time.perf_counter_ns) e gravados em arquivos CSV com as colunas sistema, bloco_MB, teste, alloc_ms, write_ms, read_ms e free_ms.

Para que cada operação fosse medida de forma separada, a alocação foi feita por mapeamento anônimo de memória (mmap), que corresponde à forma como Windows (VirtualAlloc) e Linux (mmap) entregam blocos grandes a um processo. A escrita gravou o valor 0xAB em todos os bytes do bloco; a leitura percorreu o bloco inteiro, o que também confirmou que a escrita ocorreu corretamente; e a liberação devolveu a memória ao sistema. O coletor de lixo do Python foi desativado durante a coleta. O mesmo código, sem bibliotecas externas, foi executado nos dois sistemas com a mesma versão do Python (3.14.4, 64 bits).

Os experimentos foram realizados no mesmo computador físico, com processador Intel Core i5-8300H (4 núcleos, 8 processadores lógicos), 8 GB de RAM e armazenamento SSD, com um ambiente em execução por vez e as demais aplicações fechadas. O Linux (Ubuntu 26.04.1 LTS) foi executado em uma máquina virtual VirtualBox com 4.096 MB de RAM e 2 vCPUs. O Windows ([versão do ambiente_windows.txt]) foi executado diretamente no hardware. Antes de cada coleta definitiva foi feito um teste-piloto e aplicado um intervalo de estabilização de 120 segundos.

Os arquivos CSV foram validados por um script que verificou a quantidade de registros, os tamanhos dos blocos, a numeração dos testes, duplicidades, valores ausentes, tipos de dados, tempos não negativos e a identificação do sistema. Na análise, feita com as bibliotecas pandas e matplotlib, os registros foram agrupados por sistema, tamanho do bloco e operação, e foram calculados média, mediana, desvio padrão, mínimo, máximo e quartis. Considerou-se que um sistema teve melhor desempenho em uma operação quando apresentou a menor mediana de tempo, por ser uma medida menos sensível a valores atípicos. Quando o resultado variou entre operações, a recomendação considerou o tempo total do ciclo completo. O código, os dados e as configurações estão disponíveis no repositório https://github.com/mathmehllier/benchmark-memoria-windows-linux.

**RESULTADOS E DISCUSSÃO**

Os dois arquivos CSV foram considerados válidos, com 1.000 registros cada e nenhuma inconsistência. A Figura 1 apresenta a mediana do tempo de cada operação em função do tamanho do bloco, e a Tabela 1 resume os valores para o bloco de 1.000 MB.

[INSERIR FIGURA 1 — graficos/medianas_por_operacao.png]
Figura 1 – Mediana do tempo por operação e tamanho de bloco (faixa: 1º ao 3º quartil). Fonte: os autores.

Tabela 1 – Mediana dos tempos (ms) para o bloco de 1.000 MB

| Operação | Linux | Windows | Diferença (Windows vs. Linux) |
|---|---|---|---|
| Alocação | 0,027 | [X] | [X] % |
| Escrita | 554,5 | [X] | [X] % |
| Leitura | 72,2 | [X] | [X] % |
| Liberação | 105,9 | [X] | [X] % |
| Ciclo completo | 733,0 | [X] | [X] % |

Fonte: os autores.

No Linux, a alocação manteve-se praticamente constante, em torno de 0,02 a 0,03 ms, independentemente do tamanho do bloco. Isso ocorre porque o sistema apenas reserva o espaço de endereçamento no momento da alocação, e as páginas físicas só são efetivamente atribuídas quando a memória é usada pela primeira vez. Por esse motivo, a escrita foi a operação mais custosa, crescendo de forma praticamente linear com o tamanho do bloco (cerca de 56 ms em 100 MB e 555 ms em 1.000 MB), pois inclui o tratamento das faltas de página pelo sistema operacional. A leitura e a liberação também cresceram linearmente, mas em escala menor.

[COMPLETAR COM OS RESULTADOS DO WINDOWS: comportamento da alocação, se a escrita foi mais rápida ou mais lenta, diferença percentual média em cada operação e qual sistema venceu na maioria dos tamanhos de bloco. Ver resultados/comparacao.csv e a Figura 2.]

[INSERIR FIGURA 2 — graficos/diferenca_percentual.png]
Figura 2 – Diferença percentual entre as medianas do Windows e do Linux, por operação. Fonte: os autores.

É importante observar que diferenças percentuais grandes na alocação representam valores absolutos muito pequenos (frações de milissegundo), enquanto a escrita concentra a maior parte do tempo do ciclo. Por isso, para o cenário de integração, o tempo do ciclo completo é o indicador mais relevante. Além disso, como o Linux foi executado em máquina virtual e o Windows diretamente no hardware, parte da diferença observada pode ser atribuída à virtualização, que adiciona custo ao gerenciamento de páginas de memória.

**CONSIDERAÇÕES FINAIS**

O trabalho desenvolveu e executou um microbenchmark reprodutível para comparar o desempenho das operações de alocação, escrita, leitura e liberação de memória no Windows e no Linux, com dados validados e analisados estatisticamente. [COMPLETAR: qual sistema teve menor tempo no ciclo completo e em quais operações cada um se destacou.] Com base nesses dados, a recomendação preliminar à empresa é [Windows/Linux] para as próximas avaliações do processo de integração.

Essa recomendação deve ser considerada preliminar, pois os ambientes não foram totalmente equivalentes: o Linux foi executado em máquina virtual e o Windows diretamente no hardware, e o computador possuía apenas 8 GB de RAM. Como trabalhos futuros, sugere-se repetir o experimento com os dois sistemas em máquinas virtuais idênticas ou em dual boot, e avaliar cargas mais próximas de um processo de integração real, com várias alocações simultâneas e troca de dados entre serviços.

**Palavras-chave:** Sistemas operacionais. Gerenciamento de memória. Microbenchmark. Cidades inteligentes. Ciência de dados.

**REFERÊNCIAS BIBLIOGRÁFICAS**

GEORGES, A.; BUYTAERT, D.; EECKHOUT, L. Statistically rigorous Java performance evaluation. In: ACM SIGPLAN CONFERENCE ON OBJECT-ORIENTED PROGRAMMING, SYSTEMS, LANGUAGES AND APPLICATIONS (OOPSLA), 22., 2007, Montreal. **Proceedings** [...]. New York: ACM, 2007. p. 57-76. DOI: 10.1145/1297027.1297033.

NAM, T.; PARDO, T. A. Conceptualizing smart city with dimensions of technology, people, and institutions. In: ANNUAL INTERNATIONAL DIGITAL GOVERNMENT RESEARCH CONFERENCE, 12., 2011, College Park. **Proceedings** [...]. New York: ACM, 2011. p. 282-291. DOI: 10.1145/2037556.2037602.

TANENBAUM, A. S.; BOS, H. **Sistemas operacionais modernos**. 4. ed. São Paulo: Pearson, 2016.
