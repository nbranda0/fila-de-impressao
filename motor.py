"""Simulador acadêmico de impressão: eventos discretos e prioridade dinâmica.

O relógio usa minutos inteiros, cada impressora opera a 2 páginas/minuto.
O projeto não imprime documentos reais nem coleta dados pessoais.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from heapq import heapify, heappop, heappush
from math import ceil
from typing import Iterable


@dataclass
class Documento:
    codigo: int
    nome: str
    paginas: int
    categoria: str
    chegada: int
    status: str = "AGENDADO"
    inicio: int | None = None
    conclusao: int | None = None
    impressora_id: int | None = None
    sla_cumprido: bool | None = None
    justificativa: str = ""


@dataclass(order=True)
class Evento:
    minuto: int
    ordem_tipo: int
    sequencia: int
    tipo: str = field(compare=False)
    codigo: int = field(compare=False)
    impressora_id: int | None = field(compare=False, default=None)


@dataclass
class Impressora:
    identificador: int
    documento_id: int | None = None
    inicio: int | None = None
    fim_previsto: int | None = None


class SimuladorImpressao:
    """Controla uma fila central compartilhada por duas impressoras virtuais.

    Estruturas de dados:
      - heap para eventos futuros (chegadas e conclusões);
      - lista de documentos em espera, reordenada no despacho;
      - dicionário por código para acesso direto e auditoria.
    """

    PRIORIDADE_BASE = {"NORMAL": 1, "URGENTE": 3}
    SLA_MINUTOS = {"NORMAL": 20, "URGENTE": 10}
    MINUTOS_POR_PONTO = 5
    PAGINAS_POR_MINUTO = 2
    ESTADOS = {"NORMAL": "Operação normal", "PROVAS": "Semana de provas", "URGENCIA": "Sobrecarga de urgência"}

    def __init__(self, apoio_preditivo: bool = True) -> None:
        self.apoio_preditivo = apoio_preditivo
        self._previsao_habilitada = True
        self._apoio_preventivo = False
        self.ultimo_apoio: dict | None = None
        self.minuto_atual = 0
        self.documentos: dict[int, Documento] = {}
        self.fila: list[Documento] = []
        self.concluidos: list[Documento] = []
        self.cancelados: list[Documento] = []
        self.impressoras = {1: Impressora(1), 2: Impressora(2)}
        self._eventos: list[Evento] = []
        self._proximo_codigo = 1
        self._sequencia = 0
        self._provas_ativo = False
        self._urgencia_ativa = False
        self.estado = "NORMAL"
        self.historico: list[dict] = []
        self._ultima_acao: tuple[str, tuple[int, ...], tuple[str, ...]] | None = None

    def _log(self, tipo: str, detalhes: str, codigo: int | None = None, impressora: int | None = None) -> None:
        self.historico.append({
            "id": len(self.historico) + 1,
            "minuto": self.minuto_atual,
            "tipo": tipo,
            "codigo": codigo,
            "impressora": impressora,
            "estado": self.estado,
            "fila_aguardando": len(self.fila),
            "detalhes": detalhes,
        })

    def _agendar(self, minuto: int, tipo: str, codigo: int, impressora: int | None = None) -> None:
        self._sequencia += 1
        ordem_tipo = 0 if tipo == "CONCLUSAO" else 1
        heappush(self._eventos, Evento(minuto, ordem_tipo, self._sequencia, tipo, codigo, impressora))

    @staticmethod
    def _validar(nome: str, paginas: int, categoria: str, chegada: int, atual: int) -> tuple[str, str]:
        if not isinstance(nome, str) or not nome.strip():
            raise ValueError("Informe o nome do documento.")
        if len(nome.strip()) > 100:
            raise ValueError("O nome deve ter no máximo 100 caracteres.")
        if type(paginas) is not int or not (1 <= paginas <= 2000):
            raise ValueError("A quantidade de páginas deve estar entre 1 e 2000.")
        if not isinstance(categoria, str) or categoria.strip().upper() not in ("NORMAL", "URGENTE"):
            raise ValueError("Categoria inválida: escolha NORMAL ou URGENTE.")
        if type(chegada) is not int or chegada < atual:
            raise ValueError("O minuto da chegada não pode ser anterior ao relógio atual.")
        return nome.strip(), categoria.strip().upper()

    def agendar_documento(self, nome: str, paginas: int, categoria: str, chegada: int) -> int:
        return self.adicionar_lote([(nome, paginas, categoria, chegada)])[0]

    def adicionar_lote(self, pedidos: Iterable[tuple[str, int, str, int]]) -> list[int]:
        """Adiciona vários pedidos atomicamente, processando chegadas do mesmo minuto juntas."""
        pedidos = list(pedidos)
        if not pedidos:
            return []
        if len(pedidos) > 250:
            raise ValueError("Máximo de 250 documentos por lote.")
        validados = [(*self._validar(n, p, c, t, self.minuto_atual), p, t) for n, p, c, t in pedidos]
        codigos = []
        for nome, categoria, paginas, chegada in validados:
            codigo = self._proximo_codigo
            self._proximo_codigo += 1
            self.documentos[codigo] = Documento(codigo, nome, paginas, categoria, chegada)
            self._agendar(chegada, "CHEGADA", codigo)
            codigos.append(codigo)
        self._processar_ate(self.minuto_atual)
        self._ultima_acao = ("ADICAO", tuple(codigos), ())
        return codigos

    def prioridade(self, doc: Documento) -> int:
        espera = (doc.inicio if doc.inicio is not None else self.minuto_atual) - doc.chegada
        return self.PRIORIDADE_BASE[doc.categoria] + max(0, espera) // self.MINUTOS_POR_PONTO

    def _chave(self, doc: Documento) -> tuple[int, int, int, int]:
        return (-self.prioridade(doc), doc.paginas, doc.chegada, doc.codigo)

    def fila_ordenada(self) -> list[Documento]:
        return sorted(self.fila, key=self._chave)

    def _atualizar_estado(self) -> None:
        fila_total = len(self.fila)
        urgentes = sum(d.categoria == "URGENTE" for d in self.fila)
        if fila_total >= 10:
            self._provas_ativo = True
        elif fila_total <= 6:
            self._provas_ativo = False
        if urgentes >= 5:
            self._urgencia_ativa = True
        elif urgentes <= 2:
            self._urgencia_ativa = False
        novo = "URGENCIA" if self._urgencia_ativa else "PROVAS" if self._provas_ativo else "NORMAL"
        if novo != self.estado:
            anterior = self.estado
            self.estado = novo
            self._log("ESTADO", f"{self.ESTADOS[anterior]} → {self.ESTADOS[novo]}. "
                  f"Fila: {fila_total} documento(s), {urgentes} urgente(s).")
            if novo == "NORMAL":
                self._log("RECURSO", "Impressora 2 retorna ao standby após concluir o trabalho em andamento, se houver.", impressora=2)
            elif anterior == "NORMAL":
                self._log("RECURSO", "Impressora 2 ativada para apoiar a fila.", impressora=2)
            elif novo == "URGENCIA":
                self._log("RECURSO", "Impressora 2 assume atendimento preferencial de urgências.", impressora=2)
            elif anterior == "URGENCIA":
                self._log("RECURSO", "Impressora 2 retorna ao atendimento geral.", impressora=2)
        if self._previsao_habilitada:
            self._avaliar_apoio_preventivo()

    def _projetar_inicios(self, codigos: tuple[int, ...], *, apoiar: bool) -> dict[int, int]:
        """Projeta o início de pedidos conhecidos sem alterar a simulação real.

        Usa um clone do próprio motor para respeitar páginas, chegadas futuras,
        aging, impressoras ocupadas e transições operacionais. O monitor fica
        desativado no clone para impedir recursão.
        """
        copia = deepcopy(self)
        copia._previsao_habilitada = False
        copia._apoio_preventivo = apoiar
        copia.historico = []  # Logs do clone não fazem parte da auditoria real.
        copia._despachar()  # Despacha solicitações que estão aguardando agora.
        pendentes = set(codigos)
        while any(copia.documentos[c].inicio is None for c in pendentes):
            if not copia._eventos:
                raise RuntimeError("A projeção ficou sem eventos para concluir os pedidos.")
            copia._processar_ate(copia._eventos[0].minuto)
        return {c: copia.documentos[c].inicio for c in codigos}

    def prever_slas(self) -> list[dict]:
        """Previsão dos SLAs para pedidos não iniciados, dado o cenário atual.

        A estimativa considera chegadas já agendadas, mas não prevê novas
        solicitações aleatórias que ainda não foram cadastradas.
        """
        pendentes = [d for d in self.documentos.values() if d.status in ("AGUARDANDO", "AGENDADO")]
        if not pendentes:
            return []
        inicios = self._projetar_inicios(tuple(d.codigo for d in pendentes), apoiar=self._apoio_preventivo)
        previsao = []
        for d in pendentes:
            inicio = inicios[d.codigo]
            espera = inicio - d.chegada
            limite = self.SLA_MINUTOS[d.categoria]
            previsao.append({
                "ID": d.codigo, "Documento": d.nome, "Categoria": d.categoria,
                "Páginas": d.paginas, "Chegada": d.chegada,
                "Início previsto": inicio, "Espera prevista": espera,
                "Limite SLA": limite, "Risco de violação": espera > limite,
            })
        return sorted(previsao, key=lambda p: (not p["Risco de violação"], p["Início previsto"], p["ID"]))

    def _avaliar_apoio_preventivo(self) -> None:
        """Ativa a segunda impressora antes de uma sobrecarga evitável de SLA.

        Não muda os prazos dos SLAs e não altera a ordem de impressões já
        iniciadas. Quando ativado, o apoio é mantido até esvaziar a espera ou
        entrar em um estado de sobrecarga tradicional.
        """
        if self.estado != "NORMAL":
            self._apoio_preventivo = False  # Os estados especiais já ativam a impressora 2.
            return
        if self._apoio_preventivo:
            if not self.fila:
                self._apoio_preventivo = False
                self._log("PREVISAO", "Apoio preventivo encerrado: sem pedidos aguardando.", impressora=2)
            return
        if not self.apoio_preditivo or not self.fila:
            return
        # A decisão considera os documentos já presentes na fila. Pedidos
        # agendados para o futuro serão avaliados quando chegarem.
        codigos = tuple(d.codigo for d in self.fila)
        sem_apoio = self._projetar_inicios(codigos, apoiar=False)
        com_apoio = self._projetar_inicios(codigos, apoiar=True)
        def violados(inicios: dict[int, int]) -> int:
            return sum(inicios[d.codigo] - d.chegada > self.SLA_MINUTOS[d.categoria]
                       for d in self.fila)
        antes, depois = violados(sem_apoio), violados(com_apoio)
        if depois < antes:
            self._apoio_preventivo = True
            self.ultimo_apoio = {"minuto": self.minuto_atual, "antes": antes, "depois": depois}
            self._log("PREVISAO", f"Risco estimado de SLA: {antes} → {depois} pedido(s). "
                      "Impressora 2 ativada antecipadamente.", impressora=2)

    def _motivo(self, escolhido: Documento, candidatos: list[Documento], preferencial: bool) -> str:
        demais = [d for d in candidatos if d.codigo != escolhido.codigo]
        if preferencial and escolhido.categoria == "URGENTE" and any(d.categoria == "NORMAL" for d in self.fila):
            return "Preferência por urgência"
        if not demais:
            return "Único pedido disponível"
        segundo = min(demais, key=self._chave)
        if self.prioridade(escolhido) != self.prioridade(segundo):
            return "Maior prioridade efetiva"
        if escolhido.paginas != segundo.paginas:
            return "Desempate: menos páginas"
        if escolhido.chegada != segundo.chegada:
            return "Desempate: chegada mais antiga"
        return "Desempate: ID mais antigo"

    def _iniciar(self, impressora: Impressora, preferencial: bool) -> None:
        if impressora.documento_id is not None or not self.fila:
            return
        candidatos = self.fila
        if preferencial:
            urgentes = [d for d in self.fila if d.categoria == "URGENTE"]
            if urgentes:
                candidatos = urgentes
        escolhido = min(candidatos, key=self._chave)
        justificativa = self._motivo(escolhido, candidatos, preferencial)
        self.fila.remove(escolhido)
        escolhido.status = "IMPRIMINDO"
        escolhido.inicio = self.minuto_atual
        escolhido.impressora_id = impressora.identificador
        escolhido.sla_cumprido = escolhido.inicio - escolhido.chegada <= self.SLA_MINUTOS[escolhido.categoria]
        escolhido.justificativa = justificativa
        impressora.documento_id = escolhido.codigo
        impressora.inicio = self.minuto_atual
        impressora.fim_previsto = self.minuto_atual + ceil(escolhido.paginas / self.PAGINAS_POR_MINUTO)
        self._log("INICIO", f"{escolhido.nome}; {escolhido.paginas} página(s); espera "
                  f"{escolhido.inicio - escolhido.chegada} min; {justificativa}; "
                  f"SLA {'OK' if escolhido.sla_cumprido else 'violado'}.",
                  escolhido.codigo, impressora.identificador)
        self._agendar(impressora.fim_previsto, "CONCLUSAO", escolhido.codigo, impressora.identificador)

    def _despachar(self) -> None:
        """Usa fila central: preferencial (P2) escolhe primeiro no estado vermelho."""
        ordem = [2, 1] if self.estado == "URGENCIA" else [1, 2]
        for identificador in ordem:
            impressora = self.impressoras[identificador]
            if identificador == 2 and self.estado == "NORMAL" and not self._apoio_preventivo:
                continue  # Se já estiver imprimindo, termina sem pegar outro.
            self._iniciar(impressora, preferencial=(identificador == 2 and self.estado == "URGENCIA"))

    def _processar_ate(self, destino: int) -> None:
        while self._eventos and self._eventos[0].minuto <= destino:
            instante = self._eventos[0].minuto
            self.minuto_atual = instante
            mesmo_instante: list[Evento] = []
            while self._eventos and self._eventos[0].minuto == instante:
                mesmo_instante.append(heappop(self._eventos))
            # Evento.__lt__: conclusão, chegada, sequência de cadastro.
            for evento in sorted(mesmo_instante):
                doc = self.documentos[evento.codigo]
                if evento.tipo == "CHEGADA":
                    if doc.status != "AGENDADO":
                        continue
                    doc.status = "AGUARDANDO"
                    self.fila.append(doc)
                    self._log("CHEGADA", f"{doc.nome}; {doc.paginas} página(s); {doc.categoria}.", doc.codigo)
                elif evento.tipo == "CONCLUSAO":
                    imp = self.impressoras[evento.impressora_id]
                    if imp.documento_id != doc.codigo or doc.status != "IMPRIMINDO":
                        raise RuntimeError("Conclusão sem impressão correspondente.")
                    doc.status = "CONCLUIDO"
                    doc.conclusao = instante
                    self.concluidos.append(doc)
                    imp.documento_id = None
                    imp.inicio = None
                    imp.fim_previsto = None
                    self._log("CONCLUSAO", f"{doc.nome} finalizado na impressora {imp.identificador}.", doc.codigo, imp.identificador)
                else:
                    raise RuntimeError(f"Tipo de evento desconhecido: {evento.tipo}")
            self._atualizar_estado()
            self._despachar()
        self.minuto_atual = destino

    def avancar(self, minutos: int) -> None:
        if type(minutos) is not int or minutos <= 0:
            raise ValueError("O avanço deve ser um número inteiro positivo de minutos.")
        self._ultima_acao = None
        self._processar_ate(self.minuto_atual + minutos)

    def proximo_evento(self) -> bool:
        if not self._eventos:
            return False
        self._ultima_acao = None
        self._processar_ate(self._eventos[0].minuto)
        return True

    def _remover_agendamento(self, codigo: int) -> None:
        self._eventos = [e for e in self._eventos if not (e.tipo == "CHEGADA" and e.codigo == codigo)]
        heapify(self._eventos)

    def _cancelar_interno(self, doc: Documento, tipo_evento: str = "CANCELAMENTO") -> None:
        if doc.status == "AGENDADO":
            self._remover_agendamento(doc.codigo)
        elif doc.status == "AGUARDANDO":
            self.fila.remove(doc)
        else:
            raise ValueError("Só é possível cancelar documentos agendados ou aguardando.")
        doc.status = "CANCELADO"
        self.cancelados.append(doc)
        self._log(tipo_evento, f"{doc.nome} cancelado antes de iniciar a impressão.", doc.codigo)
        self._atualizar_estado()
        self._despachar()

    def cancelar(self, codigo: int) -> None:
        doc = self.documentos.get(codigo)
        if doc is None:
            raise ValueError("Documento não encontrado.")
        status_anterior = doc.status
        self._cancelar_interno(doc)
        self._ultima_acao = ("CANCELAMENTO", (codigo,), (status_anterior,))

    def pode_desfazer(self) -> bool:
        if not self._ultima_acao:
            return False
        acao, codigos, _ = self._ultima_acao
        if acao == "CANCELAMENTO":
            return all(self.documentos[c].status == "CANCELADO" for c in codigos)
        return all(self.documentos[c].status in ("AGENDADO", "AGUARDANDO") for c in codigos)

    def desfazer(self) -> bool:
        if not self.pode_desfazer():
            return False
        acao, codigos, anteriores = self._ultima_acao
        self._ultima_acao = None
        if acao == "ADICAO":
            for codigo in codigos:
                self._cancelar_interno(self.documentos[codigo], "DESFAZER")
        else:
            doc = self.documentos[codigos[0]]
            self.cancelados.remove(doc)
            status_anterior = anteriores[0]
            doc.status = status_anterior
            if status_anterior == "AGENDADO":
                self._agendar(doc.chegada, "CHEGADA", doc.codigo)
            else:
                self.fila.append(doc)
            self._log("DESFAZER", f"Cancelamento de {doc.nome} revertido.", doc.codigo)
            self._atualizar_estado()
            self._despachar()
        return True

    def documentos_agendados(self) -> list[Documento]:
        return sorted((d for d in self.documentos.values() if d.status == "AGENDADO"), key=lambda d: (d.chegada, d.codigo))

    def urgentes_aguardando(self) -> int:
        return sum(d.categoria == "URGENTE" for d in self.fila)

    def status_impressora(self, identificador: int) -> str:
        imp = self.impressoras[identificador]
        if imp.documento_id is not None:
            return "FINALIZANDO" if identificador == 2 and self.estado == "NORMAL" else "IMPRIMINDO"
        if identificador == 2 and self.estado == "NORMAL" and not self._apoio_preventivo:
            return "STANDBY"
        return "DISPONIVEL"

    def progresso(self, identificador: int) -> float:
        imp = self.impressoras[identificador]
        if imp.documento_id is None:
            return 0.0
        duracao = imp.fim_previsto - imp.inicio
        return max(0.0, min(1.0, (self.minuto_atual - imp.inicio) / duracao))

    def tabela_fila(self) -> list[dict]:
        return [{
            "Posição": i, "ID": d.codigo, "Documento": d.nome, "Páginas": d.paginas,
            "Categoria": d.categoria, "Chegada": d.chegada,
            "Espera": self.minuto_atual - d.chegada, "Prioridade": self.prioridade(d),
            "SLA": "No prazo" if self.minuto_atual - d.chegada <= self.SLA_MINUTOS[d.categoria] else "Vencido",
        } for i, d in enumerate(self.fila_ordenada(), 1)]

    def tabela_agenda(self) -> list[dict]:
        return [{"ID": d.codigo, "Documento": d.nome, "Chegada": d.chegada,
                 "Em": d.chegada - self.minuto_atual, "Páginas": d.paginas, "Categoria": d.categoria}
                for d in self.documentos_agendados()]

    def tabela_concluidos(self) -> list[dict]:
        return [{"ID": d.codigo, "Documento": d.nome, "Páginas": d.paginas,
                 "Impressora": d.impressora_id, "Espera": d.inicio - d.chegada,
                 "Início": d.inicio, "Conclusão": d.conclusao,
                 "SLA": "Cumprido" if d.sla_cumprido else "Violado"} for d in self.concluidos]

    def metricas(self) -> dict:
        iniciados = [d for d in self.documentos.values() if d.inicio is not None]
        esperas = [d.inicio - d.chegada for d in iniciados]
        violados = sum(d.sla_cumprido is False for d in iniciados)
        return {"aguardando": len(self.fila), "urgentes": self.urgentes_aguardando(),
                "agendados": len(self.documentos_agendados()), "concluidos": len(self.concluidos),
                "cancelados": len(self.cancelados), "tempo_medio": sum(esperas) / len(esperas) if esperas else 0,
                "sla_violados": violados, "sla_cumpridos": len(iniciados) - violados}

    def exportar_sql(self) -> str:
        """SQL integral executável no SQLite: snapshots de documentos e auditoria de eventos."""
        def esc(valor: str) -> str:
            return "'" + valor.replace("'", "''") + "'"

        def opt_num(valor: int | None) -> str:
            return "NULL" if valor is None else str(valor)

        linhas = [
            "-- Fila de Impressão: dados acadêmicos fictícios e minutos virtuais.",
            "BEGIN TRANSACTION;",
            "CREATE TABLE IF NOT EXISTS documentos (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, "
            "paginas INTEGER NOT NULL, categoria TEXT NOT NULL, chegada INTEGER NOT NULL, "
            "inicio INTEGER, conclusao INTEGER, impressora INTEGER, status TEXT NOT NULL, sla_cumprido INTEGER);",
            "CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY, minuto INTEGER NOT NULL, "
            "tipo TEXT NOT NULL, documento_id INTEGER, impressora INTEGER, estado TEXT NOT NULL, "
            "fila_aguardando INTEGER NOT NULL, detalhes TEXT NOT NULL);",
        ]
        for d in sorted(self.documentos.values(), key=lambda x: x.codigo):
            sla = "NULL" if d.sla_cumprido is None else str(int(d.sla_cumprido))
            linhas.append(f"INSERT INTO documentos VALUES ({d.codigo},{esc(d.nome)},{d.paginas},{esc(d.categoria)},"
                          f"{d.chegada},{opt_num(d.inicio)},{opt_num(d.conclusao)},{opt_num(d.impressora_id)},"
                          f"{esc(d.status)},{sla});")
        for e in self.historico:
            linhas.append(f"INSERT INTO auditoria VALUES ({e['id']},{e['minuto']},{esc(e['tipo'])},"
                          f"{opt_num(e['codigo'])},{opt_num(e['impressora'])},{esc(e['estado'])},"
                          f"{e['fila_aguardando']},{esc(e['detalhes'])});")
        linhas.append("COMMIT;")
        return "\n".join(linhas) + "\n"
