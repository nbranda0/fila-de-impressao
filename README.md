# Fila de Impressão

**Projeto acadêmico — Simulador de Filas de Prioridade**  
**Tecnologias:** Python 3.10+, Streamlit, programação orientada a objetos e SQL (SQLite).

Simulação de uma central universitária de impressões. **Versão 1.1: monitor preditivo de SLA e ativação preventiva da segunda impressora.** O programa recebe documentos fictícios, agenda chegadas, calcula prioridades dinâmicas, simula duas impressoras e registra eventos auditáveis. **Não imprime arquivos físicos** e não possui integração com impressoras reais.

## Executar no VS Code / Windows

1. Extraia a pasta `fila_de_impressao` e abra **a própria pasta** no VS Code (Arquivo → Abrir Pasta).
2. Abra **Terminal → Novo Terminal** (PowerShell).
3. Instale as dependências:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Execute:

   ```powershell
   python -m streamlit run app.py
   ```

5. Abra o endereço indicado no terminal, normalmente `http://localhost:8501`.

Para parar: clique no terminal e pressione `Ctrl+C`. Ao editar arquivos, salve com `Ctrl+S`; o Streamlit oferece atualização/reexecução da página.

> Se o `python` não funcionar, verifique se ele está instalado com `python --version`. O projeto foi planejado para a versão Streamlit 1.67 instalada no computador do aluno, mas usa APIs que também estão disponíveis em versões recentes anteriores.

## Como demonstrar rapidamente

- **Teste básico:** cadastre um documento de 10 páginas no minuto 0, um urgente no minuto 0 e use **Próximo evento**.
- **Semana de provas:** abra **Geração em lote e cenários de demonstração**, escolha **Semana de provas** e clique em **Adicionar cenário**. O sistema ativa a segunda impressora ao detectar 10+ documentos aguardando.
- **Sobrecarga de urgência:** reinicie, selecione **Sobrecarga de urgência** e adicione o cenário. A segunda impressora atende preferencialmente urgentes.
- **Aging:** cadastre um documento longo normal (30 páginas) no minuto 0 para ocupar a primeira impressora. Ainda no minuto 0, cadastre outro documento normal. Agende um urgente no minuto 14 e avance 15 minutos. O documento normal aguardando terá prioridade efetiva 4, o urgente recém-chegado terá prioridade 3.
- **Previsão de atraso:** inicie uma impressão longa (100 páginas) e, ainda no minuto 0, cadastre um segundo documento normal (2 páginas). A impressora 2 é ativada antecipadamente, mesmo com menos de 10 documentos na fila, para evitar uma violação prevista.
- **Auditoria:** clique em **Exportar auditoria SQL**, salve `logs.sql` e abra o arquivo. Ele contém a criação de duas tabelas e registros SQL executáveis no SQLite.

**Importante:** adicionar cenários acrescenta solicitações à simulação existente; não apaga a fila atual. Reinicie antes de cada demonstração independente.

## Estados automáticos

| Estado | Entrada | Saída (histerese) | Segunda impressora |
|---|---|---|---|
| Normal (azul) | Condições especiais não ativas | — | Standby, exceto quando o monitor prevê atrasos evitáveis; pode atuar como apoio preventivo |
| Semana de provas (laranja) | 10+ aguardando | 6 ou menos | Atende fila geral |
| Sobrecarga de urgência (vermelho) | 5+ urgentes aguardando | 2 ou menos | Prefere urgentes; se não houver, atende normais |

Contagens consideram **apenas documentos aguardando**, não os já em impressão. O estado vermelho prevalece visualmente sobre o laranja; os dois indicadores internos podem permanecer ativos de forma independente. Os limites são verificados em cada ciclo de evento e após cancelamentos. Se duas condições mudarem durante o mesmo instante, o sistema conclui impressões e registra todas as chegadas **antes** de atualizar o estado e distribuir novos documentos.

### Monitor preditivo de SLA (v1.1)

Além dos gatilhos por quantidade de documentos, o sistema **projeta os inícios de impressão** dos pedidos conhecidos usando uma cópia isolada do motor. Essa projeção considera número de páginas, chegadas agendadas, prioridades, aging, impressoras ocupadas e os estados automáticos. O clone não altera a simulação nem seus logs.

Em operação normal, antes do despacho, o monitor compara duas projeções para os documentos **já aguardando**: (a) seguir somente com a impressora 1 e (b) ativar imediatamente a impressora 2. Se (b) reduzir o número de violações previstas, ativa a impressora 2 **como apoio preventivo**, mesmo com menos de 10 documentos na fila. Essa ativação é registrada no histórico; o apoio permanece até acabar a espera ou até um dos estados especiais assumir o controle. A cor do estado continua azul, pois a condição de sobrecarga formal não mudou.

Na seção **Indicadores**, o painel **Previsão de SLA** apresenta quantos pedidos **ainda não iniciados** correm risco de esperar mais que o prazo. O detalhe mostra o minuto previsto de início, a espera prevista e o limite de cada pedido. **SLAs já violados** continuam contabilizados separadamente; não se apagam violações antigas.

**Limitações:** é uma previsão condicional, não uma garantia. Novos documentos ainda não cadastrados podem mudar o resultado; duas impressoras podem ser insuficientes, especialmente quando chegam muitos documentos longos. A decisão proativa só é tomada quando a ativação antecipada prevê redução de pelo menos uma violação entre os pedidos já aguardando.


## Algoritmo

- NORMAL: prioridade inicial 1; URGENTE: prioridade inicial 3.
- A cada 5 minutos **completos** de espera, a prioridade aumenta 1 ponto (*aging*).
- Ordem geral: **maior prioridade efetiva → menos páginas → chegada mais antiga → menor ID**.
- Não há preempção: uma impressão iniciada não é interrompida.
- No estado vermelho, a impressora 2 seleciona primeiro entre os urgentes; a impressora 1 mantém o algoritmo geral.
- Cada impressora processa **2 páginas/minuto**. Duração: `ceil(paginas / 2)` minutos.
- Metas simuladas de espera (**não são SLAs reais de instituições**): 10 min (urgente), 20 min (normal). O SLA considera espera **até o início da impressão**; não é garantia de atendimento.

## Estrutura

```text
fila_de_impressao/
├── app.py                   # Interface web Streamlit
├── motor.py                 # Entidades, eventos e regras de simulação
├── catalogo.py              # 22 documentos fictícios e cenários
├── demo.py                  # Exemplo reproduzível sem Streamlit
├── requirements.txt         # Dependência Streamlit
├── .streamlit/config.toml   # Tema azul claro
├── assets/README.md         # Como disponibilizar a logo offline
├── docs/
│   ├── proposta.md
│   ├── arquitetura.md
│   └── diagrama_classes.mmd
├── tests/test_motor.py      # Testes automatizados
└── README.md
```

## Testes automatizados

```powershell
python -m unittest discover -s tests -v
```

O núcleo é testável sem instalar Streamlit. Os **26 testes automatizados** cobrem aging, SJF no desempate, simultaneidade, cancelamento/desfazer, mudanças operacionais, duas impressoras, SLA, previsão sem mutação de estado, acionamento preventivo, regressão de dois lotes e execução do SQL em memória.

## Controles importantes

- **+1 min / +5 min**: avança o tempo simulado; o sistema processa eventos intermediários.
- **Próximo evento**: salta até a próxima chegada agendada ou conclusão.
- **Dado**: gera imediatamente 1 documento aleatório com nome entre 22 tipos, páginas dentro da faixa e 25% de chance de urgência.
- **Lote**: gera 5, 10 ou 20 documentos aleatórios no minuto atual.
- **Cenários**: casos reproduzíveis para testar modo normal, semana de provas ou sobrecarga.
- **Excluir (✕)**: cancela **somente** documentos ainda aguardando ou agendados, registrando o cancelamento na auditoria.
- **Desfazer**: reverte a última inclusão ou exclusão **ainda pendente**, quando o relógio não avançou. Não volta o tempo e não interrompe impressões em andamento. Se o último pedido já entrou em impressão, desfazer essa inclusão fica indisponível.
- **Reiniciar**: apaga a sessão atual após confirmação; exporte antes se quiser guardar os logs.

## Auditoria

O botão **Exportar auditoria SQL** produz `logs.sql` com `BEGIN TRANSACTION`, esquema SQL e `INSERT`s nas tabelas `documentos` e `auditoria`. O arquivo é executável em SQLite. O histórico inclui mudanças de estado e de recursos, chegadas, inícios, conclusões, cancelamentos e reversões. **Exportação é manual**; sem banco externo ou persistência entre sessões.

## Uso acadêmico, autoria e publicação

O projeto foi estruturado com apoio de IA. A equipe deve revisar, testar, adaptar e documentar sua própria participação, observando as regras da disciplina. Não atribua commits ou contribuições a pessoas que não as fizeram.

Para publicar no GitHub: crie um repositório público, inclua estes arquivos, mantenha o `.gitignore`, documente os commits verdadeiros de cada integrante e adicione um README com instruções. Se desejar publicar o site, o Streamlit Community Cloud pode executar `app.py` a partir desse repositório; a publicação na internet é opcional em relação ao manual fornecido.

## Atenção à logo

A interface tenta carregar a marca institucional da página oficial da UNIFACS. Para garantir que o logo funcione **sem internet e na hospedagem**, salve uma cópia do arquivo de logo autorizado como `assets/logo_unifacs.png`. Se a imagem não carregar, será exibido o texto **UNIFACS**. Não há vínculo ou endosso institucional implícito.
