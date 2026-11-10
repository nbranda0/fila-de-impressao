"""Pequena demonstração de eventos sem usar Streamlit.

Execute: python demo.py
"""
from catalogo import gerar_cenario
from motor import SimuladorImpressao

sim = SimuladorImpressao()
sim.adicionar_lote(gerar_cenario("Semana de provas", 0))
print("Estado inicial:", sim.ESTADOS[sim.estado])
for i in (1, 2):
    imp = sim.impressoras[i]
    nome = sim.documentos[imp.documento_id].nome if imp.documento_id else "livre"
    print(f"Impressora {i}: {nome}")
print("Aguardando:", len(sim.fila))
while sim.proximo_evento() and sim.minuto_atual < 30:
    print(f"Minuto {sim.minuto_atual:02d}: concluídos={len(sim.concluidos)}; aguardando={len(sim.fila)}; estado={sim.ESTADOS[sim.estado]}")
print("Use o botão Exportar auditoria SQL na interface para obter um arquivo .sql executável.")
