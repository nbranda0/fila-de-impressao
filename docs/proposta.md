# Proposta teórica — Fila de Impressão

## Problema
Em uma central acadêmica com recursos limitados, uma fila FIFO simples pode deixar pedidos urgentes aguardando trabalhos muito longos. Um escalonamento de prioridade fixa, por outro lado, pode adiar repetidamente documentos normais quando novas urgências continuam chegando (risco de *starvation*).

## Objetivo
Simular a organização de solicitações de impressão com prioridades dinâmicas e gerenciamento adaptativo de duas impressoras. O sistema deve registrar os eventos, acompanhar tempos de espera e permitir avaliar cenários de congestionamento.

## Hipótese
O uso de *aging*, associado à ativação condicional de um segundo recurso, pode reduzir esperas excessivas em cenários simulados, mantendo preferência inicial aos documentos urgentes. Isso é uma hipótese a verificar mediante testes e comparação com uma política fixa, não uma conclusão garantida.

## Regras essenciais
1. Cada documento contém ID, nome fictício, páginas, categoria e instante de chegada.
2. O relógio é virtual e avança apenas por interação do usuário.
3. A impressora 1 atende a fila geral por prioridade efetiva; o desempate é por menor trabalho e ordem de chegada.
4. A impressora 2 fica em standby durante operação normal, mas pode ser ativada preventivamente quando a simulação prevê um atraso evitável de SLA; também é ativada no congestionamento e adota preferência por urgências na sobrecarga.
5. Não há preempção de impressões iniciadas.
6. Um evento de mudança de estado fica registrado no histórico.
7. O sistema mede tempo de espera e violações de SLAs fictícios, sem prometer cumprimento em condições de demanda excessiva.
8. SQL exportado permite auditoria dos documentos e operações da sessão.

## Limitações
- Não há impressão física, autenticação, acesso a arquivos reais ou cálculo de gasto energético.
- Os tempos por página e SLAs foram escolhidos para facilitar a simulação, não representam dados oficiais da instituição.
- O aging reduz o risco de starvation, mas não elimina qualquer atraso em cargas ilimitadas ou arbitrárias.
- O monitor preditivo considera documentos conhecidos e não pode prever pedidos que ainda não foram cadastrados; duas impressoras nem sempre serão suficientes para cumprir todos os prazos.
- A logo institucional é usada apenas para contextualização acadêmica; não constitui endosso.

## Evidências sugeridas para a apresentação
Print do modo normal; print da transição para semana de provas e da segunda impressora; print de sobrecarga com suporte preferencial; exemplo de empate resolvido por número de páginas; histórico SQL e testes automatizados.
