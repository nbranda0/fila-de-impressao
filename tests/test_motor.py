import sqlite3
import unittest

from motor import SimuladorImpressao


class TestMotor(unittest.TestCase):
    def test_impressao_com_relogio_virtual(self):
        s = SimuladorImpressao()
        s.agendar_documento("A", 5, "NORMAL", 0)
        self.assertEqual(s.impressoras[1].documento_id, 1)
        self.assertEqual(s.status_impressora(2), "STANDBY")
        s.avancar(2)
        self.assertAlmostEqual(s.progresso(1), 2/3)
        s.avancar(1)
        self.assertEqual(s.concluidos[0].conclusao, 3)
        self.assertEqual(s.status_impressora(1), "DISPONIVEL")

    def test_aging_supera_urgente_recente(self):
        s = SimuladorImpressao()
        s.agendar_documento("Ocupado", 30, "NORMAL", 0)
        s.agendar_documento("Antigo", 8, "NORMAL", 0)
        s.agendar_documento("Novo", 2, "URGENTE", 14)
        s.avancar(15)
        self.assertEqual(s.documentos[s.impressoras[1].documento_id].nome, "Antigo")

    def test_mais_paginas_perde_desempate(self):
        s = SimuladorImpressao()
        s.agendar_documento("Ocupado", 20, "NORMAL", 0)
        s.adicionar_lote([("Longo", 40, "NORMAL", 1), ("Curto", 2, "NORMAL", 1)])
        s.avancar(10)
        self.assertEqual(s.documentos[s.impressoras[1].documento_id].nome, "Curto")

    def test_criterio_deterministico_id(self):
        s = SimuladorImpressao()
        s.agendar_documento("Ocupado", 20, "NORMAL", 0)
        s.adicionar_lote([("Primeiro", 2, "NORMAL", 1), ("Segundo", 2, "NORMAL", 1)])
        s.avancar(10)
        self.assertEqual(s.documentos[s.impressoras[1].documento_id].nome, "Primeiro")
        self.assertIn("ID", s.documentos[s.impressoras[1].documento_id].justificativa)

    def test_conclusao_e_chegada_mesmo_minuto(self):
        s = SimuladorImpressao()
        s.agendar_documento("Ocupado", 4, "NORMAL", 0)
        s.agendar_documento("Normal", 2, "NORMAL", 0)
        s.agendar_documento("Urgente", 2, "URGENTE", 2)
        s.avancar(2)
        self.assertEqual(s.documentos[s.impressoras[1].documento_id].nome, "Urgente")
        self.assertEqual(len(s.concluidos), 1)
        self.assertEqual([x["tipo"] for x in s.historico if x["minuto"] == 2][:2], ["CONCLUSAO", "CHEGADA"])

    def test_semana_de_provas_ativa_segunda(self):
        s = SimuladorImpressao()
        s.adicionar_lote([(f"Doc {i}", 10, "NORMAL", 0) for i in range(12)])
        self.assertEqual(s.estado, "PROVAS")
        self.assertEqual(s.status_impressora(2), "IMPRIMINDO")
        self.assertEqual(len(s.fila), 10)
        self.assertNotEqual(s.impressoras[1].documento_id, s.impressoras[2].documento_id)

    def test_sobrecarga_ativa_preferencial(self):
        s = SimuladorImpressao()
        s.agendar_documento("Bloqueio", 100, "NORMAL", 0)
        s.adicionar_lote([("Antigo normal", 2, "NORMAL", 0)] +
                         [(f"Urgente {i}", 10, "URGENTE", 0) for i in range(6)])
        self.assertEqual(s.estado, "URGENCIA")
        d2 = s.documentos[s.impressoras[2].documento_id]
        self.assertEqual(d2.categoria, "URGENTE")
        self.assertIn("urgência", d2.justificativa)

    def test_transicao_histerese(self):
        s = SimuladorImpressao(apoio_preditivo=False)
        s.agendar_documento("Bloqueio", 200, "NORMAL", 0)
        s.adicionar_lote([(f"Doc {i}", 5, "NORMAL", 0) for i in range(11)])
        self.assertEqual(s.estado, "PROVAS")
        # 10 em espera antes do segundo despacho -> 9; deve permanecer em provas.
        self.assertEqual(len(s.fila), 10)
        for d in s.fila[:3]:
            s.cancelar(d.codigo)
        self.assertEqual(len(s.fila), 7)
        self.assertEqual(s.estado, "PROVAS")
        s.cancelar(s.fila[0].codigo)
        self.assertEqual(s.estado, "NORMAL")
        self.assertEqual(s.status_impressora(2), "FINALIZANDO")
        s.avancar(3)
        self.assertEqual(s.status_impressora(2), "STANDBY")

    def test_sla_e_metricas(self):
        s = SimuladorImpressao(apoio_preditivo=False)
        s.agendar_documento("Bloqueio", 50, "NORMAL", 0)
        s.agendar_documento("Esperando", 2, "NORMAL", 0)
        s.avancar(25)
        self.assertFalse(s.documentos[s.impressoras[1].documento_id].sla_cumprido)
        self.assertEqual(s.metricas()["sla_violados"], 1)

    def test_cancela_agendado_e_pula_evento(self):
        s = SimuladorImpressao()
        i = s.agendar_documento("Futuro", 2, "URGENTE", 13)
        s.cancelar(i)
        self.assertFalse(s.proximo_evento())
        self.assertEqual(s.documentos[i].status, "CANCELADO")

    def test_desfazer_cancelamento(self):
        s = SimuladorImpressao()
        a = s.agendar_documento("Primeiro", 20, "NORMAL", 0)
        b = s.agendar_documento("Segundo", 2, "NORMAL", 0)
        s.cancelar(b)
        self.assertTrue(s.desfazer())
        self.assertEqual(s.documentos[b].status, "AGUARDANDO")
        self.assertTrue(any(x["tipo"] == "DESFAZER" for x in s.historico))

    def test_desfazer_adicao_pendente(self):
        s = SimuladorImpressao()
        s.agendar_documento("Ocupado", 20, "NORMAL", 0)
        b = s.agendar_documento("Novo", 2, "NORMAL", 0)
        self.assertTrue(s.pode_desfazer())
        self.assertTrue(s.desfazer())
        self.assertEqual(s.documentos[b].status, "CANCELADO")

    def test_desfazer_nao_retrocede_tempo(self):
        s = SimuladorImpressao()
        s.agendar_documento("Ocupado", 20, "NORMAL", 0)
        s.agendar_documento("Pendente", 2, "NORMAL", 0)
        s.avancar(1)
        self.assertFalse(s.pode_desfazer())

    def test_sql_auditoria_executavel(self):
        s = SimuladorImpressao()
        s.agendar_documento("D'Ávila", 2, "NORMAL", 0)
        s.avancar(1)
        with sqlite3.connect(":memory:") as conn:
            conn.executescript(s.exportar_sql())
            tipos = [x[0] for x in conn.execute("SELECT tipo FROM auditoria ORDER BY id")]
            self.assertEqual(tipos, ["CHEGADA", "INICIO", "CONCLUSAO"])
            self.assertEqual(conn.execute("SELECT nome FROM documentos").fetchone()[0], "D'Ávila")

    def test_monitor_ativa_segunda_antes_de_dez_documentos(self):
        s = SimuladorImpressao()
        s.agendar_documento("Longa impressão", 100, "NORMAL", 0)
        d = s.agendar_documento("Pedido em risco", 2, "NORMAL", 0)
        self.assertEqual(s.estado, "NORMAL")
        self.assertEqual(s.impressoras[2].documento_id, d)
        self.assertTrue(s._apoio_preventivo)
        self.assertEqual(s.ultimo_apoio["antes"], 1)
        self.assertEqual(s.ultimo_apoio["depois"], 0)
        self.assertEqual(s.metricas()["sla_violados"], 0)

    def test_monitor_nao_altera_sla_nem_falsifica_historico(self):
        s = SimuladorImpressao()
        s.agendar_documento("Apostila", 100, "NORMAL", 0)
        s.agendar_documento("Relatório", 2, "NORMAL", 0)
        historico = list(s.historico)
        minutos = s.minuto_atual
        previstos = s.prever_slas()
        self.assertEqual(minutos, s.minuto_atual)
        self.assertEqual(historico, s.historico)
        self.assertEqual(s.SLA_MINUTOS, {"NORMAL": 20, "URGENTE": 10})
        self.assertTrue(all("Espera prevista" in p for p in previstos))
        self.assertFalse(any(p["Risco de violação"] for p in previstos))

    def test_previsao_sinaliza_risco_inevitavel_sem_alterar_fatos(self):
        s = SimuladorImpressao()
        s.adicionar_lote([
            ("Lenta A", 200, "NORMAL", 0),
            ("Lenta B", 200, "NORMAL", 0),
            ("Lenta C", 200, "NORMAL", 0),
            ("Lenta D", 200, "NORMAL", 0),
        ])
        prev = s.prever_slas()
        self.assertTrue(any(p["Risco de violação"] for p in prev))
        self.assertEqual(s.metricas()["sla_violados"], 0)
        s.avancar(210)
        self.assertGreater(s.metricas()["sla_violados"], 0)

    def test_apoio_preventivo_encerra_apos_fila_esvaziar(self):
        s = SimuladorImpressao()
        s.agendar_documento("Longa", 100, "NORMAL", 0)
        s.agendar_documento("Curta", 2, "NORMAL", 0)
        s.avancar(1)
        self.assertEqual(s.status_impressora(2), "STANDBY")
        self.assertFalse(s._apoio_preventivo)

    def test_comparacao_monitor_ligado_e_desligado(self):
        dados = [("Longa", 100, "NORMAL", 0), ("Curta", 2, "NORMAL", 0)]
        desligado = SimuladorImpressao(apoio_preditivo=False)
        ligado = SimuladorImpressao(apoio_preditivo=True)
        for s in (desligado, ligado):
            for doc in dados:
                s.agendar_documento(*doc)
            s.avancar(60)
        self.assertGreater(desligado.metricas()["sla_violados"], ligado.metricas()["sla_violados"])

    def test_regressao_dia_tranquilo_mais_dois_lotes(self):
        """Reproduz a sequência de uso relatada com sorteios controlados."""
        import random
        from catalogo import gerar_cenario, gerar_lote

        def executar(monitor: bool) -> int:
            s = SimuladorImpressao(apoio_preditivo=monitor)
            s.adicionar_lote(gerar_cenario("Dia tranquilo", 0))
            rng = random.Random(8)
            s.adicionar_lote(gerar_lote(5, 0, rng))
            cancelar = next((d for d in s.fila if d.categoria == "NORMAL"), None)
            if cancelar is None:
                cancelar = s.documentos_agendados()[0]
            s.cancelar(cancelar.codigo)
            s.adicionar_lote(gerar_lote(5, 0, rng))
            s.avancar(500)
            return s.metricas()["sla_violados"]

        self.assertEqual(executar(False), 4)
        self.assertEqual(executar(True), 0)

    def test_validacoes(self):
        s = SimuladorImpressao()
        for dados in [("", 2, "NORMAL", 0), ("A", 0, "NORMAL", 0),
                      ("A", 2, "VIP", 0), ("A", 2, "NORMAL", -1)]:
            with self.assertRaises(ValueError):
                s.agendar_documento(*dados)
        with self.assertRaises(ValueError):
            s.avancar(0)

    def test_proximo_evento(self):
        s = SimuladorImpressao()
        s.agendar_documento("A", 2, "NORMAL", 0)
        self.assertTrue(s.proximo_evento())
        self.assertEqual(s.minuto_atual, 1)
        self.assertFalse(s.proximo_evento())


if __name__ == "__main__":
    unittest.main()
