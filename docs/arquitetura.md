# Arquitetura do Simulador

## Modelo orientado a objetos

- `Documento`: entidade de domínio com ID, nome, páginas, urgência, chegada, estado e horários.
- `Evento`: registro imutável de instante, tipo, sequência e documento a ser processado. A ordenação compara minuto, tipo e sequência.
- `Impressora`: recurso com identificador, documento atual e intervalo de execução.
- `SimuladorImpressao`: coordena fila central, relógio virtual, eventos, prioridades, estados operacionais e auditoria.

`catalogo.py` gera dados sintéticos, sem misturar sorteios ao motor. `app.py` consome o motor e apresenta os resultados visualmente. Isso torna testes do núcleo independentes do Streamlit.

## Estruturas de dados

| Estrutura | Uso | Motivo |
|---|---|---|
| `heapq` (heap mínimo) | Agenda de eventos futuros | Obtém o próximo evento em O(log E) para inserção e remoção. |
| `list[Documento]` | Fila central de espera | Prioridade muda com o tempo; ordenação é recalculada a cada despacho. |
| `dict[int, Documento]` | Registro de documentos | Acesso por ID médio O(1), sem percorrer a fila. |
| `list[dict]` | Auditoria em memória | Mantém sequência das mudanças da simulação; exportação SQL manual. |

Ordenar a lista de espera custa **O(N log N)** por despacho, adequado ao escopo acadêmico. A fila de espera não é o heap de eventos: o heap ordena **quando** os eventos acontecerão, enquanto a fila central determina **qual** documento deve ser atendido.

## Eventos simultâneos

Para um mesmo minuto, a ordem é: (1) conclusões, (2) chegadas, (3) atualização de estado, (4) distribuição para impressoras, (5) logs correspondentes às operações. Eventos de mesmo tipo respeitam o número de sequência. Uma chegada no mesmo minuto de uma conclusão participa da próxima escolha.

## Estados e recursos

O estado operacional combina dois indicadores com histerese (provas e urgência); o vermelho tem precedência visual. O modo é recalculado a cada **ciclo de processamento** e após cancelamentos. A segunda impressora pode continuar ocupada mesmo após o sistema voltar ao normal; ao concluir, permanece em standby. Essa decisão evita interromper impressões em andamento.

Em sobrecarga, a impressora 2 escolhe primeiro entre urgentes quando estiver livre e a impressora 1 mantém a seleção geral. Ambas compartilham a mesma lista, sem duplicidade.

## Monitor de previsão e ativação preventiva

O `SimuladorImpressao` compara dois futuros simulados em **cópias independentes do estado atual**: operação normal e operação com segunda impressora de apoio. O método `_projetar_inicios` desabilita o próprio monitor nos clones (sem recursão), processa chegadas/conclusões na mesma ordem do motor real e projeta o horário de início dos pedidos pendentes.

No estado NORMAL, caso haja documentos aguardando e a projeção da segunda impressora reduza violações de SLA, `_avaliar_apoio_preventivo` ativa a segunda impressora sem mudar o estado visual para PROVAS. O apoio persiste até a fila de espera esvaziar ou um estado especial assumir, e cada alteração fica no log `PREVISAO`. O método `prever_slas` devolve a estimativa atual dos pedidos em espera ou agendados para exibição na interface.

A previsão não promete cumprimento de SLA nem considera futuros documentos não cadastrados. Seu cálculo envolve executar uma simulação auxiliar, portanto o custo cresce com a quantidade de eventos; é adequado ao limite de lotes deste simulador didático, mas não seria uma solução apropriada para grandes volumes de produção sem otimização.

## Cancelamento e reversão

A exclusão só é permitida para documentos `AGENDADO` ou `AGUARDANDO`. Início e conclusão não podem ser revertidos pelo botão. Desfazer usa a última operação registrada e, quando permitido, grava uma ação compensatória no histórico; não apaga o histórico anterior nem retrocede o relógio.

## SQL

A exportação cria as tabelas `documentos` e `auditoria` e insere registros com os valores de minuto virtual. Aspas são escapadas e campos ausentes usam `NULL`. O arquivo resultante é executável no SQLite. Não existe escrita automática em disco nem sincronização entre sessões de diferentes visitantes.
