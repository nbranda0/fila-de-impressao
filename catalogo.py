"""Documentos fictícios e cenários reproduzíveis do simulador."""
from __future__ import annotations

import random

# Nome, mínimo de páginas, máximo de páginas.
DOCUMENTOS = [
    ("Currículo para Estágio", 1, 3),
    ("Comprovante de Matrícula", 1, 2),
    ("Declaração Acadêmica", 1, 3),
    ("Formulário de Estágio", 2, 5),
    ("Capa de Trabalho", 1, 2),
    ("Fichamento de Leitura", 3, 8),
    ("Resumo de Algoritmos", 3, 10),
    ("Lista de Exercícios", 5, 15),
    ("Exercícios de POO", 4, 12),
    ("Slides de Seminário", 5, 15),
    ("Trabalho de POO", 8, 20),
    ("Trabalho de Redes", 10, 25),
    ("Relatório de Laboratório", 6, 18),
    ("Relatório de A3", 10, 25),
    ("Projeto de Pesquisa", 12, 30),
    ("Artigo Acadêmico", 8, 22),
    ("Relatório de Estágio", 12, 35),
    ("Material de Revisão", 15, 35),
    ("Apostila de Python", 30, 80),
    ("Apostila de Cálculo", 40, 100),
    ("Manual de Estudos", 25, 60),
    ("Rascunho de TCC", 30, 90),
]


def sortear(minuto: int, rng: random.Random | None = None) -> tuple[str, int, str, int]:
    """25% urgentes; faixa de páginas depende do tipo de documento."""
    rng = rng or random.Random()
    nome, minimo, maximo = rng.choice(DOCUMENTOS)
    paginas = rng.randint(minimo, maximo)
    categoria = "URGENTE" if rng.random() < 0.25 else "NORMAL"
    return nome, paginas, categoria, minuto


def gerar_lote(quantidade: int, minuto: int, rng: random.Random | None = None) -> list[tuple[str, int, str, int]]:
    if quantidade not in (5, 10, 20):
        raise ValueError("Escolha 5, 10 ou 20 documentos.")
    rng = rng or random.Random()
    return [sortear(minuto, rng) for _ in range(quantidade)]


def gerar_cenario(nome: str, minuto: int) -> list[tuple[str, int, str, int]]:
    """Cenários com distribuição fixa de categorias; nunca apagam a fila existente."""
    if nome == "Dia tranquilo":
        rng = random.Random(101)
        return [("Currículo para Estágio", 2, "NORMAL", minuto),
                ("Lista de Exercícios", 10, "NORMAL", minuto + 4),
                ("Relatório de A3", 12, "URGENTE", minuto + 9)]
    if nome == "Semana de provas":
        rng = random.Random(202)
        categorias = ["NORMAL"] * 10 + ["URGENTE"] * 2
    elif nome == "Sobrecarga de urgência":
        rng = random.Random(303)
        categorias = ["URGENTE"] * 7 + ["NORMAL"] * 2
    else:
        raise ValueError("Cenário inválido.")
    rng.shuffle(categorias)
    pedidos = []
    for categoria in categorias:
        titulo, minimo, maximo = rng.choice(DOCUMENTOS)
        pedidos.append((titulo, rng.randint(minimo, maximo), categoria, minuto))
    return pedidos
