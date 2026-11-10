import random
import unittest

from catalogo import DOCUMENTOS, gerar_cenario, gerar_lote, sortear


class TestCatalogo(unittest.TestCase):
    def test_22_modelos_e_intervalos(self):
        self.assertEqual(len(DOCUMENTOS), 22)
        for titulo, inferior, superior in DOCUMENTOS:
            self.assertTrue(titulo)
            self.assertLessEqual(1, inferior)
            self.assertLessEqual(inferior, superior)

    def test_sorteio_deterministico_com_semente(self):
        a = sortear(7, random.Random(42))
        b = sortear(7, random.Random(42))
        self.assertEqual(a, b)
        self.assertEqual(a[3], 7)
        self.assertIn(a[2], ("NORMAL", "URGENTE"))

    def test_lote(self):
        docs = gerar_lote(10, 23, random.Random(15))
        self.assertEqual(len(docs), 10)
        self.assertTrue(all(x[3] == 23 for x in docs))

    def test_cenarios_carga(self):
        provas = gerar_cenario("Semana de provas", 4)
        urgencia = gerar_cenario("Sobrecarga de urgência", 4)
        self.assertEqual(len(provas), 12)
        self.assertEqual(sum(d[2] == "URGENTE" for d in provas), 2)
        self.assertEqual(len(urgencia), 9)
        self.assertEqual(sum(d[2] == "URGENTE" for d in urgencia), 7)
        self.assertTrue(all(d[3] == 4 for d in provas + urgencia))


if __name__ == "__main__":
    unittest.main()
