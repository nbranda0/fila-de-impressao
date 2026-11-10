"""Fila de Impressão — interface Streamlit do simulador acadêmico."""
from __future__ import annotations

from html import escape
from pathlib import Path
import base64

import streamlit as st

from catalogo import gerar_cenario, gerar_lote, sortear
from motor import Documento, SimuladorImpressao

st.set_page_config(page_title="Fila de Impressão", page_icon="🖨️", layout="wide", initial_sidebar_state="collapsed")

ESTILOS = {
    "NORMAL": {"titulo": "Operação normal", "cor": "#3B82C4", "leve": "#E8F2FD", "texto": "A impressora 2 está em standby."},
    "PROVAS": {"titulo": "Semana de provas", "cor": "#D58C25", "leve": "#FFF2DC", "texto": "Fila elevada: as duas impressoras atendem pedidos."},
    "URGENCIA": {"titulo": "Sobrecarga de urgência", "cor": "#D85454", "leve": "#FCEBEC", "texto": "A impressora 2 prioriza solicitações urgentes."},
}


def tempo(minutos: int) -> str:
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def seguro(valor: object) -> str:
    return escape(str(valor), quote=True)


def cabecalho_logo() -> str:
    caminho = Path(__file__).parent / "assets" / "logo_unifacs.png"
    if caminho.exists():
        dados = base64.b64encode(caminho.read_bytes()).decode("ascii")
        src = f"data:image/png;base64,{dados}"
    else:
        # URL de imagem institucional oficial; para uso offline, salve a logo em assets/logo_unifacs.png.
        src = "https://www.unifacs.br/assets/img/logo-unifacs.svg"
    return f'<span class="logo-fallback">UNIFACS</span><img class="logo-oficial" alt="Logo da UNIFACS" src="{src}">'


if "simulador" not in st.session_state:
    st.session_state.simulador = SimuladorImpressao()
sim: SimuladorImpressao = st.session_state.simulador
modo = ESTILOS[sim.estado]
texto_estado = ("A impressora 2 foi ativada preventivamente para reduzir o risco de atraso."
                if sim.estado == "NORMAL" and sim._apoio_preventivo else modo["texto"])

st.markdown(f"""
<style>
:root {{--acento:{modo['cor']};--acento-claro:{modo['leve']};}}
.stApp {{background: #F5F8FD; color:#20354D;}}
.block-container {{max-width:1280px; padding-top:1.2rem; padding-bottom:2.5rem;}}
#MainMenu, footer {{visibility:hidden;}}
header[data-testid="stHeader"] {{background: transparent;}}
section[data-testid="stSidebar"] {{background:#F4F8FD;}}
.stButton>button, .stFormSubmitButton>button {{border-radius:10px; border:1px solid #D7E4F1; font-weight:600;}}
.stButton>button[kind="primary"], .stFormSubmitButton>button[kind="primary"] {{background:#3278B7; color:white; border-color:#3278B7;}}
div[data-testid="stMetric"] {{background:white;border:1px solid #DEE9F4;border-radius:14px;padding:13px 15px;}}
div[data-testid="stMetricLabel"] {{color:#71849A;}}
[data-testid="stVerticalBlockBorderWrapper"] {{border-radius:14px;}}
.header-band {{display:flex; align-items:center; justify-content:space-between; gap:18px; padding:12px 16px; background:white; border:1px solid #DCE7F3; border-radius:15px; margin-bottom:14px;}}
.brand {{display:flex; align-items:center; gap:16px; min-width:0;}}
.logo-frame {{position:relative; display:flex; width:145px; height:48px; align-items:center;justify-content:center;border-right:1px solid #E1EAF3;padding-right:15px;}}
.logo-oficial {{position:absolute; width:130px;height:42px;object-fit:contain;background:white;}}
.logo-fallback {{color:#144B91;font-size:16px;font-weight:800;letter-spacing:.03em;}}
.brand-title {{font-weight:800;font-size:22px;color:#1C466E;line-height:1.1;}}
.brand-subtitle {{font-size:12px;color:#71849A;margin-top:4px;}}
.clock {{text-align:right;flex-shrink:0;}}
.clock-label {{color:#6B8096;font-size:11px;}}
.clock-time {{color:#1A456E;font-weight:800;font-size:27px;font-variant-numeric:tabular-nums;line-height:1.1;}}
.state-panel {{background:var(--acento-claro);border:1px solid var(--acento);border-left:5px solid var(--acento);padding:11px 15px;border-radius:12px;margin:2px 0 16px;}}
.state-name {{font-weight:800;color:var(--acento);font-size:15px;}}
.state-desc {{color:#4B5E70;font-size:12px;margin-top:3px;}}
.section-name {{color:#20496F;font-size:18px;font-weight:750;margin:10px 0 9px;}}
.section-sub {{color:#76889C;font-size:12px;margin:0 0 9px;}}
.flow-grid {{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:3px 0 16px;}}
.flow-step {{background:white;border:1px solid #DCE8F3;border-radius:11px;padding:11px 13px;}}
.flow-step strong {{display:block;color:#254F78;font-size:20px;font-variant-numeric:tabular-nums;}}
.flow-step span {{color:#71849A;font-size:12px;}}
.printer-card {{min-height:188px;background:white;border:1px solid #D9E6F2;border-top:3px solid var(--acento);border-radius:14px;padding:16px;margin-bottom:6px;}}
.printer-top {{display:flex;justify-content:space-between;gap:12px;align-items:center;}}
.printer-name {{color:#234B72;font-weight:800;font-size:16px;}}
.status {{font-size:11px;font-weight:700;color:#63809A;}}
.status.printing {{color:#248366;}}
.status.standby {{color:#98A5B5;}}
.printer-doc {{color:#2B4B6B;font-weight:700;margin-top:18px;margin-bottom:3px;font-size:14px;word-break:break-word;}}
.printer-meta {{font-size:12px;color:#7C8DA0;margin-top:3px;}}
.progress-track {{width:100%;height:8px;background:#E8EFF6;border-radius:100px;margin-top:11px;overflow:hidden;}}
.progress-fill {{height:100%;background:var(--acento);border-radius:100px;}}
.printer-reason {{color:#8A9BAD;font-size:11px;margin-top:10px;}}
.job-card {{background:white;border:1px solid #D9E6F2;border-left:3px solid #7CABD4;padding:10px 12px;border-radius:11px;margin-bottom:6px;}}
.job-card.urgent {{border-left-color:#E3A143;}}
.job-card.overdue {{border-left-color:#D75B5B;}}
.job-top {{display:flex;align-items:center;justify-content:space-between;gap:6px;}}
.job-title {{font-size:13px;font-weight:750;color:#294B6B;overflow-wrap:anywhere;}}
.job-meta {{color:#7C8FA3;font-size:11px;margin-top:4px;}}
.job-tag {{color:#68819B;font-size:10px;background:#EDF3FA;border-radius:99px;padding:3px 8px;white-space:nowrap;}}
.job-tag.urgent {{background:#FFF0DC;color:#A66C23;}}
.job-tag.overdue {{background:#FCE7E7;color:#B94F4F;}}
.number {{font-weight:850;color:#3476B8;margin-right:8px;}}
.empty-card {{background:white;border:1px dashed #CBDDEB;border-radius:12px;padding:20px 13px;color:#8A9BAD;text-align:center;font-size:13px;}}
.small-note {{color:#8796A8;font-size:11px;margin:5px 0 12px;}}
.done-card {{background:white;border:1px solid #D9E6F2;border-left:3px solid #67B39A;border-radius:11px;padding:12px 14px;margin:4px 0;}}
.done-title {{color:#294B6B;font-weight:750;font-size:13px;overflow-wrap:anywhere;}}
.done-meta {{color:#8190A1;font-size:11px;margin-top:4px;}}
.done-bad {{color:#BC5353;}}
.done-good {{color:#248366;}}
.forecast-box {{background:#FFFFFF;border:1px solid #DDE8F3;border-radius:12px;padding:11px 13px;margin:10px 0 8px;}}
.forecast-box.risk {{border-left:3px solid #D89A3A;}}
.forecast-box.safe {{border-left:3px solid #67B39A;}}
.forecast-title {{color:#234B72;font-size:13px;font-weight:750;}}
.forecast-description {{color:#7C8FA3;font-size:11px;margin-top:5px;line-height:1.4;}}
.preventive-note {{color:#356F9D;font-size:12px;margin-top:7px;}}

/* Controles do Streamlit: contraste consistente em temas claro ou escuro. */
.stApp button[data-testid^="stBaseButton"],
.stApp div.stButton > button,
.stApp div.stFormSubmitButton > button,
.stApp div.stDownloadButton > button,
.stApp div[data-testid="stPopover"] > button {{
  background-color: #FFFFFF !important;
  color: #24547D !important;
  border: 1px solid #C9DAEC !important;
  border-radius: 10px !important;
  box-shadow: 0 1px 2px rgba(23, 66, 112, .04) !important;
}}
.stApp button[data-testid^="stBaseButton"] *,
.stApp div.stButton > button *,
.stApp div.stFormSubmitButton > button *,
.stApp div.stDownloadButton > button * {{
  color: inherit !important;
}}
.stApp button[data-testid^="stBaseButton"]:hover:not(:disabled),
.stApp div.stButton > button:hover:not(:disabled),
.stApp div.stFormSubmitButton > button:hover:not(:disabled) {{
  background-color: #E7F2FD !important;
  color: #164E7B !important;
  border-color: #8EB6DB !important;
}}
.stApp button[data-testid="stBaseButton-primary"],
.stApp div.stButton > button[kind="primary"],
.stApp div.stFormSubmitButton > button[kind="primary"] {{
  background-color: #3278B7 !important;
  border-color: #3278B7 !important;
  color: #FFFFFF !important;
}}
.stApp button[data-testid="stBaseButton-primary"]:hover:not(:disabled),
.stApp div.stButton > button[kind="primary"]:hover:not(:disabled),
.stApp div.stFormSubmitButton > button[kind="primary"]:hover:not(:disabled) {{
  background-color: #24659E !important;
  border-color: #24659E !important;
  color: #FFFFFF !important;
}}
.stApp button[data-testid^="stBaseButton"]:disabled,
.stApp div.stButton > button:disabled,
.stApp div.stFormSubmitButton > button:disabled {{
  background-color: #EEF3F8 !important;
  border-color: #DCE6F1 !important;
  color: #95A5B6 !important;
  opacity: 1 !important;
  cursor: not-allowed;
}}
/* Campos do formulário também ficam legíveis se o visitante estiver no modo escuro. */
.stApp div[data-baseweb="input"],
.stApp div[data-baseweb="select"] > div,
.stApp div[data-baseweb="textarea"] {{
  background-color: #FFFFFF !important;
  color: #20354D !important;
}}
.stApp div[data-baseweb="input"] input,
.stApp div[data-baseweb="textarea"] textarea {{
  color: #20354D !important;
}}
.stApp div[data-baseweb="select"] * {{
  color: #20354D !important;
}}

@media (max-width: 750px) {{
 .brand-title {{font-size:17px;}}
 .logo-frame {{width:95px;padding-right:8px;}}
 .logo-oficial {{width:85px;}}
 .brand {{gap:9px;}}
 .clock-time {{font-size:21px;}}
 .flow-grid {{grid-template-columns:repeat(2,minmax(0,1fr));}}
}}
</style>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="header-band">
  <div class="brand"><div class="logo-frame">{cabecalho_logo()}</div>
    <div><div class="brand-title">Fila de Impressão</div><div class="brand-subtitle">Simulador acadêmico · UNIFACS</div></div>
  </div>
  <div class="clock"><div class="clock-label">RELÓGIO VIRTUAL · MINUTO {sim.minuto_atual}</div>
    <div class="clock-time">{tempo(sim.minuto_atual)}</div></div>
</div>
<div class="state-panel"><div class="state-name">{seguro(modo['titulo'])}</div>
<div class="state-desc">{seguro(texto_estado)} · {len(sim.fila)} aguardando, {sim.urgentes_aguardando()} urgentes.</div></div>
""", unsafe_allow_html=True)

# Controles do relógio, desfazer, dado e reinício.
c = st.columns([1, 1, 1.45, 1.35, 1.2, 1.05], gap="small")
if c[0].button("+1 min", use_container_width=True):
    sim.avancar(1)
    st.rerun()
if c[1].button("+5 min", use_container_width=True):
    sim.avancar(5)
    st.rerun()
if c[2].button("⏭ Próximo evento", use_container_width=True, disabled=not sim._eventos):
    sim.proximo_evento()
    st.rerun()
if c[3].button("🎲 Aleatório", use_container_width=True, help="Cria um documento no minuto atual"):
    sim.agendar_documento(*sortear(sim.minuto_atual))
    st.rerun()
if c[4].button("↶ Desfazer", use_container_width=True, disabled=not sim.pode_desfazer(),
               help="Reverte a última inclusão ou exclusão ainda pendente, se o tempo não avançou"):
    sim.desfazer()
    st.rerun()
with c[5].popover("↻ Reiniciar", use_container_width=True):
    st.warning("Isso reinicia o relógio e apaga o histórico desta sessão. Exporte os logs antes, se precisar.")
    if st.button("Confirmar reinício", type="primary", use_container_width=True):
        st.session_state.simulador = SimuladorImpressao()
        st.rerun()

m = sim.metricas()
st.markdown(f"""
<div class="flow-grid">
 <div class="flow-step"><strong>{m['agendados']}</strong><span>01 · Agendados</span></div>
 <div class="flow-step"><strong>{m['aguardando']}</strong><span>02 · Na fila</span></div>
 <div class="flow-step"><strong>{sum(p.documento_id is not None for p in sim.impressoras.values())}</strong><span>03 · Imprimindo</span></div>
 <div class="flow-step"><strong>{m['concluidos']}</strong><span>04 · Concluídos</span></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-name">Impressoras</div>', unsafe_allow_html=True)
colunas_imp = st.columns(2, gap="medium")
for n, coluna in enumerate(colunas_imp, 1):
    imp = sim.impressoras[n]
    estado_imp = sim.status_impressora(n)
    if estado_imp == "STANDBY":
        conteudo = '<div class="printer-doc" style="color:#99A8B8">Em espera</div><div class="printer-meta">Ativa automaticamente quando a demanda aumenta.</div>'
        situacao = 'STANDBY'
        classe = 'standby'
    elif imp.documento_id is None:
        conteudo = '<div class="printer-doc" style="color:#7C95AC">Disponível</div><div class="printer-meta">Aguardando próximo pedido</div>'
        situacao = 'DISPONÍVEL'
        classe = ''
    else:
        doc = sim.documentos[imp.documento_id]
        porcentagem = sim.progresso(n) * 100
        resto = imp.fim_previsto - sim.minuto_atual
        conteudo = (f'<div class="printer-doc">{seguro(doc.nome)}</div>'
                    f'<div class="printer-meta">{doc.paginas} páginas · {doc.categoria} · termina em {resto} min</div>'
                    f'<div class="progress-track"><div class="progress-fill" style="width:{porcentagem:.1f}%"></div></div>'
                    f'<div class="printer-meta">{porcentagem:.0f}% concluído</div>'
                    f'<div class="printer-reason">ⓘ {seguro(doc.justificativa)}</div>')
        situacao = 'FINALIZANDO' if estado_imp == 'FINALIZANDO' else 'IMPRIMINDO'
        classe = 'printing'
    if n == 2 and sim.estado == "URGENCIA":
        nome_imp = 'Impressora 2 · Preferencial'
    elif n == 2 and sim._apoio_preventivo and sim.estado == "NORMAL":
        nome_imp = 'Impressora 2 · Preventiva'
    else:
        nome_imp = f'Impressora {n}'
    coluna.markdown(f'<div class="printer-card"><div class="printer-top"><div class="printer-name">▣ {seguro(nome_imp)}</div>'
                   f'<div class="status {classe}">● {situacao}</div></div>{conteudo}</div>', unsafe_allow_html=True)

area_principal, area_lateral = st.columns([1.75, 1], gap="large")
with area_principal:
    st.markdown(f'<div class="section-name">Fila de espera <span style="color:#8D9DAC;font-size:13px;font-weight:500">· {len(sim.fila)} documentos</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Maior prioridade → menos páginas → chegada mais antiga → ID</div>', unsafe_allow_html=True)
    with st.container(height=390, border=False):
        fila = sim.fila_ordenada()
        if not fila:
            st.markdown('<div class="empty-card">Nenhum documento aguardando. Experimente adicionar um pedido.</div>', unsafe_allow_html=True)
        for pos, doc in enumerate(fila, 1):
            espera = sim.minuto_atual - doc.chegada
            atrasado = espera > sim.SLA_MINUTOS[doc.categoria]
            classe = 'overdue' if atrasado else ('urgent' if doc.categoria == 'URGENTE' else '')
            etiqueta = 'SLA vencido' if atrasado else doc.categoria
            l, r = st.columns([8, 1.2], vertical_alignment="center", gap="small")
            l.markdown(f'<div class="job-card {classe}"><div class="job-top"><div class="job-title"><span class="number">{pos:02d}</span>{seguro(doc.nome)}</div>'
                       f'<div class="job-tag {classe}">{seguro(etiqueta)}</div></div>'
                       f'<div class="job-meta">{doc.paginas} pág. · espera {espera} min · prioridade P{sim.prioridade(doc)} · chegou no min {doc.chegada}</div></div>',
                       unsafe_allow_html=True)
            if r.button("✕", key=f"cancelar_fila_{doc.codigo}", help=f"Cancelar pedido #{doc.codigo}", use_container_width=True):
                sim.cancelar(doc.codigo)
                st.rerun()
with area_lateral:
    st.markdown('<div class="section-name">Agendados</div>', unsafe_allow_html=True)
    with st.container(height=190, border=False):
        agendados = sim.documentos_agendados()
        if not agendados:
            st.markdown('<div class="empty-card">Sem chegadas futuras.</div>', unsafe_allow_html=True)
        for doc in agendados:
            l, r = st.columns([7, 1.6], vertical_alignment="center", gap="small")
            l.markdown(f'<div class="job-card {"urgent" if doc.categoria == "URGENTE" else ""}"><div class="job-title">{seguro(doc.nome)}</div>'
                       f'<div class="job-meta">{doc.paginas} pág. · chega no min {doc.chegada} · em {doc.chegada - sim.minuto_atual} min</div></div>',
                       unsafe_allow_html=True)
            if r.button("✕", key=f"cancelar_agendado_{doc.codigo}", help=f"Cancelar pedido #{doc.codigo}", use_container_width=True):
                sim.cancelar(doc.codigo)
                st.rerun()
    st.markdown('<div class="section-name">Indicadores</div>', unsafe_allow_html=True)
    a, b = st.columns(2)
    a.metric("Espera média", f"{m['tempo_medio']:.1f} min")
    b.metric("SLAs violados", str(m['sla_violados']))
    previsoes = sim.prever_slas()
    em_risco = [p for p in previsoes if p["Risco de violação"]]
    status_previsao = (f"{len(em_risco)} pedido(s) com atraso previsto" if em_risco
                       else "Nenhum atraso previsto nos pedidos conhecidos")
    classe_previsao = "risk" if em_risco else "safe"
    st.markdown(f'<div class="forecast-box {classe_previsao}">'
                f'<div class="forecast-title">◷ Previsão de SLA · {len(em_risco)} em risco</div>'
                f'<div class="forecast-description">{seguro(status_previsao)}.</div></div>',
                unsafe_allow_html=True)
    if sim._apoio_preventivo and sim.ultimo_apoio:
        st.markdown('<div class="preventive-note">ⓘ Impressora 2 em apoio preventivo: previsão indicou atraso evitável.</div>',
                    unsafe_allow_html=True)
    with st.expander("Ver projeção de esperas e prazos"):
        st.caption("Estimativas simuladas com os pedidos já conhecidos. Novas chegadas podem mudar os resultados.")
        if previsoes:
            visual = [{**{k: v for k, v in p.items() if k != "Risco de violação"},
                       "Situação": "Em risco" if p["Risco de violação"] else "No prazo"}
                      for p in previsoes]
            st.dataframe(visual, hide_index=True, use_container_width=True)
        else:
            st.caption("Nenhum pedido pendente para projetar.")
    st.markdown('<div class="small-note">SLAs simulados: normal 20 min; urgente 10 min. O limite vale até o início da impressão. Previsões não garantem cumprimento.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-name">Novas solicitações</div>', unsafe_allow_html=True)
with st.container(border=True):
    with st.form("novo_pedido", clear_on_submit=True):
        a, b, c, d = st.columns([3.2, 1, 1.3, 1.25])
        nome = a.text_input("Documento", placeholder="Ex.: Relatório de A3", max_chars=100)
        paginas = b.number_input("Páginas", min_value=1, max_value=2000, value=8, step=1)
        categoria = c.selectbox("Prioridade", ["NORMAL", "URGENTE"])
        chegada = d.number_input("Chegada (min)", min_value=sim.minuto_atual, value=sim.minuto_atual, step=1)
        enviado = st.form_submit_button("+ Cadastrar pedido", type="primary", use_container_width=True)
        if enviado:
            try:
                sim.agendar_documento(nome, int(paginas), categoria, int(chegada))
                st.rerun()
            except ValueError as erro:
                st.error(str(erro))

with st.expander("🎲 Geração em lote e cenários de demonstração"):
    l, r = st.columns(2, gap="large")
    with l:
        st.caption("**Lote aleatório** · probabilidade de 25% de urgentes")
        quantidade = st.select_slider("Número de documentos", options=[5, 10, 20], value=10)
        if st.button("Gerar lote", use_container_width=True):
            sim.adicionar_lote(gerar_lote(quantidade, sim.minuto_atual))
            st.rerun()
    with r:
        st.caption("**Cenários reproduzíveis** · acrescentam documentos à simulação")
        cenario = st.selectbox("Cenário", ["Dia tranquilo", "Semana de provas", "Sobrecarga de urgência"])
        if st.button("Adicionar cenário", use_container_width=True):
            sim.adicionar_lote(gerar_cenario(cenario, sim.minuto_atual))
            st.rerun()

st.markdown('<div class="section-name">Últimas impressões concluídas</div>', unsafe_allow_html=True)
if not sim.concluidos:
    st.markdown('<div class="empty-card">Ainda não há documentos concluídos. Avance o relógio para acompanhar o fluxo.</div>', unsafe_allow_html=True)
else:
    recentes = list(reversed(sim.concluidos[-6:]))
    colunas_finais = st.columns(min(3, len(recentes)), gap="small")
    for i, doc in enumerate(recentes):
        situacao = "SLA cumprido" if doc.sla_cumprido else "SLA violado"
        classe = "done-good" if doc.sla_cumprido else "done-bad"
        colunas_finais[i % len(colunas_finais)].markdown(
            f'<div class="done-card"><div class="done-title">✓ {seguro(doc.nome)}</div>'
            f'<div class="done-meta">{doc.paginas} pág. · Impressora {doc.impressora_id} · Espera {doc.inicio-doc.chegada} min</div>'
            f'<div class="done-meta {classe}">{situacao} · Concluído no min {doc.conclusao}</div></div>',
            unsafe_allow_html=True)

st.markdown('<div class="section-name">Histórico e dados</div>', unsafe_allow_html=True)
with st.expander(f"Impressões concluídas ({len(sim.concluidos)})"):
    if sim.concluidos:
        st.dataframe(sim.tabela_concluidos(), hide_index=True, use_container_width=True)
    else:
        st.caption("Ainda não há impressões concluídas.")
with st.expander(f"Linha do tempo de eventos ({len(sim.historico)})"):
    for evento in reversed(sim.historico[-40:]):
        st.markdown(f"**Minuto {evento['minuto']} · {evento['tipo']}** — {evento['detalhes']}")
with st.expander("Tabela técnica da fila, agenda e auditoria"):
    aba1, aba2, aba3 = st.tabs(["Fila", "Agendados", "Auditoria"])
    with aba1:
        st.dataframe(sim.tabela_fila(), hide_index=True, use_container_width=True)
    with aba2:
        st.dataframe(sim.tabela_agenda(), hide_index=True, use_container_width=True)
    with aba3:
        st.dataframe(sim.historico, hide_index=True, use_container_width=True)

st.download_button("⬇ Exportar auditoria SQL", data=sim.exportar_sql(), file_name="logs.sql",
                   mime="application/sql", use_container_width=False)
st.caption("Simulação acadêmica · documentos fictícios · nenhuma impressão física é realizada. A auditoria é exportada sob demanda; não há armazenamento persistente entre sessões.")
