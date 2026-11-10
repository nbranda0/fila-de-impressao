# Atualização v1.1 — Previsão e prevenção de violações de SLA

## Problema identificado

O monitor original acionava a segunda impressora somente com pelo menos 10 documentos aguardando ou 5 urgentes. Uma fila menor, porém composta por documentos longos, ainda podia ultrapassar os SLAs sem acionar apoio.

## O que mudou

- Monitor preditivo estima o início de impressão dos pedidos conhecidos, considerando páginas, prioridades, aging, próximas chegadas já cadastradas, ocupação das impressoras e estados automáticos.
- Em operação normal, compara a projeção **sem** e **com** a segunda impressora ativada agora, considerando os pedidos já aguardando.
- Ativa a segunda impressora antecipadamente se isso reduzir o número previsto de SLAs violados. O estado visual continua azul, com a identificação discreta `Impressora 2 · Preventiva`.
- Exibe quantos pedidos em espera/agendados estão projetados para ultrapassar o SLA. A seção recolhível mostra o minuto previsto para cada início, a espera esperada e o limite.
- Registra a decisão preventiva no histórico SQL, sem alterar SLA nem apagar violações antigas.

## Verificação

Execute `python -m unittest discover -s tests -v`.

26 testes passaram na elaboração desta versão, incluindo um caso reproduzível semelhante a `Dia tranquilo → gerar 5 → cancelar 1 → gerar 5`, com semente de sorteio fixa: **4 violações sem o monitor; 0 com ele**.

## Limites

O monitor não conhece pedidos futuros que ainda não foram registrados. Algumas filas não têm capacidade suficiente para cumprir todos os prazos, mesmo com as duas impressoras ativas. A previsão também não incorpora novas decisões preventivas futuras que ainda não ocorreram; é uma estimativa condicional ao estado presente e aos eventos conhecidos.
