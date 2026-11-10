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
    "NORMAL": {"titulo": "Operação normal", "cor": "#80BDFF", "leve": "#1A3552", "texto": "A impressora 2 está em standby."},
    "PROVAS": {"titulo": "Semana de provas", "cor": "#F7BB6F", "leve": "#402D1C", "texto": "Fila elevada: as duas impressoras atendem pedidos."},
    "URGENCIA": {"titulo": "Sobrecarga de urgência", "cor": "#FF8D9B", "leve": "#432632", "texto": "A impressora 2 prioriza solicitações urgentes."},
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

# CSS isolado da lógica: paleta escura coerente para todos os componentes.
CSS_TEMA = r"""
/* Fila de Impressão · identidade nocturna azul-petróleo · v1.2 */
:root {
  color-scheme: dark;
  --bg: #0B1628;
  --surface: #14253B;
  --surface-raised: #182D46;
  --surface-hover: #203A57;
  --border: #304B68;
  --border-soft: #263D57;
  --text: #EAF3FE;
  --text-soft: #C0D2E5;
  --muted: #A4B9D1;
  --dim: #8FA7C2;
  --blue: #83C1FF;
  --blue-strong: #54A8F1;
  --green: #71D8B9;
  --orange: #F7BF75;
  --red: #FF8FA2;
  --state: __STATE_COLOR__;
  --state-soft: __STATE_SOFT__;
}
html, body, [data-testid="stAppViewContainer"], .stApp {
  background: #0B1628 !important;
  color: var(--text);
}
.stApp {
  background-image: radial-gradient(ellipse 1000px 550px at 48% -200px, #1B3857 0%, #0B1628 70%) !important;
  color: var(--text);
}
.block-container {max-width: 1240px; padding: 1.15rem 2rem 3.3rem;}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background: transparent !important;}
section[data-testid="stSidebar"] {background: #101E31 !important;}
.stApp p, .stApp label {color: var(--text-soft);}
.stApp h1, .stApp h2, .stApp h3 {color: var(--text);}
.stApp hr {border-color: var(--border-soft);}
.stApp a {color: var(--blue);}
.stApp a:hover {color: #B6DCFF;}
/* Componentes próprios */
.header-band {
  display: flex; align-items: center; justify-content: space-between; gap: 18px;
  padding: 13px 18px; border-radius: 17px;
  background: linear-gradient(115deg, #1B314C, #12253B 75%);
  border: 1px solid #365475; box-shadow: 0 9px 28px rgba(1,10,20,.18);
  margin-bottom: 14px;
}
.brand {display:flex; align-items:center; gap:16px; min-width:0;}
.logo-frame {
  position:relative; display:flex; width:146px; height:52px;
  align-items:center; justify-content:center; border-radius:10px;
  background: #F6F9FF; flex-shrink:0; padding:5px 10px;
}
.logo-oficial {position:absolute; inset:5px 10px; width:calc(100% - 20px); height:calc(100% - 10px); object-fit:contain;}
.logo-fallback {color:#164B8B; font-size:17px; font-weight:850; letter-spacing:.02em;}
.brand-title {font-weight:800; font-size:22px; color:var(--text); line-height:1.1; letter-spacing:-.035em;}
.brand-subtitle {font-size:12px; color:var(--muted); margin-top:5px;}
.clock {text-align:right; flex-shrink:0;}
.clock-label {color:var(--muted); font-size:10px; letter-spacing:.07em; text-transform:uppercase;}
.clock-time {color:#D9EDFF; font-weight:800; font-size:28px; font-variant-numeric:tabular-nums;line-height:1.1; margin-top:4px;}
.state-panel {
  background:linear-gradient(100deg, var(--state-soft), #14253B 88%);
  border:1px solid var(--state); border-left:4px solid var(--state);
  border-radius:12px; padding:12px 15px; margin:3px 0 16px;
}
.state-name {font-weight:800; color:var(--state); font-size:14px; letter-spacing:.01em;}
.state-desc {color:var(--text-soft); font-size:12px; margin-top:4px; line-height:1.45;}
.section-name {color:var(--text);font-size:17px;font-weight:760;margin:11px 0 9px;letter-spacing:-.02em;}
.section-sub {color:var(--muted);font-size:12px;margin:0 0 10px;line-height:1.5;}
.flow-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:11px;margin:4px 0 18px;}
.flow-step {
  background: linear-gradient(145deg, #1A304A, #14253B);
  border:1px solid var(--border-soft); border-radius:12px; padding:13px 16px;
  position:relative; overflow:hidden;
}
.flow-step:before {content:"";position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--state),transparent);opacity:.8;}
.flow-step strong {display:block; color:#F0F7FE; font-size:25px; font-variant-numeric:tabular-nums; line-height:1.2;}
.flow-step span {display:block; color:var(--muted);font-size:12px;margin-top:5px;}
.printer-card {
  min-height:168px; background:linear-gradient(150deg,#1A304B,#14263D);
  border:1px solid var(--border);border-top:3px solid var(--state);
  border-radius:15px;padding:16px 17px;margin:2px 0 8px;
  box-shadow: 0 6px 22px rgba(0,0,0,.1);
}
.printer-top {display:flex;justify-content:space-between;align-items:center;gap:12px;}
.printer-name {color:var(--text);font-size:15px;font-weight:780; display:flex;align-items:center;gap:8px;}
.printer-icon {display:inline-flex;color:var(--state);opacity:.95;}
.printer-icon svg {width:19px;height:19px;}
.status {font-size:10px;font-weight:800;letter-spacing:.05em;color:var(--muted);white-space:nowrap;}
.status.printing {color:var(--green);}
.status.standby {color:var(--dim);}
.printer-doc {color:var(--text);font-weight:700;font-size:14px;margin-top:17px;margin-bottom:4px;overflow-wrap:anywhere;}
.printer-meta {color:var(--muted);font-size:12px;margin-top:5px;}
.printer-reason {color:var(--dim);font-size:11px;margin-top:10px;}
.progress-track {width:100%;height:8px;background:#0B192B;border:1px solid #294663;border-radius:99px;margin-top:14px;overflow:hidden;}
.progress-fill {height:100%;background:var(--state);border-radius:99px;transition:width .22s ease;}
.job-card {
  background:linear-gradient(130deg,#1B304A,#172940);
  border:1px solid var(--border-soft);border-left:3px solid #6DB6F8;
  border-radius:11px;padding:11px 13px;margin-bottom:7px;
}
.job-card.urgent {border-left-color:var(--orange);}
.job-card.overdue {border-left-color:var(--red);background:#2A283A;}
.job-top {display:flex;align-items:center;justify-content:space-between;gap:8px;}
.job-title {color:var(--text);font-size:13px;font-weight:740;overflow-wrap:anywhere;line-height:1.3;}
.job-meta {color:var(--muted);font-size:11px;margin-top:6px;line-height:1.5;}
.job-tag {color:#ABD6FF;background:#213D5A;border:1px solid #315777;border-radius:100px;padding:3px 8px;font-size:10px;font-weight:700;white-space:nowrap;}
.job-tag.urgent {color:#FFCF90;background:#49351E;border-color:#7A562B;}
.job-tag.overdue {color:#FFC0CA;background:#512D39;border-color:#884956;}
.number {color:#8BC7FF;font-weight:850;margin-right:10px;font-variant-numeric:tabular-nums;}
.empty-card {background:#12233A;border:1px dashed #36526F;border-radius:12px;padding:22px 14px;color:var(--muted);text-align:center;font-size:12px;line-height:1.6;}
.small-note {color:var(--muted);font-size:11px;margin:7px 0 13px;line-height:1.5;}
.done-card {background:linear-gradient(145deg,#1A3047,#14263B);border:1px solid var(--border-soft);border-left:3px solid var(--green);border-radius:12px;padding:13px 15px;margin:5px 0;min-height:98px;}
.done-title {color:var(--text);font-weight:740;font-size:13px;overflow-wrap:anywhere;}
.done-meta {color:var(--muted);font-size:11px;margin-top:6px;line-height:1.45;}
.done-bad {color:var(--red);}
.done-good {color:var(--green);}
.forecast-box {background:#182C44;border:1px solid var(--border-soft);border-radius:12px;padding:12px 14px;margin:10px 0 8px;}
.forecast-box.risk {border-left:3px solid var(--orange);}
.forecast-box.safe {border-left:3px solid var(--green);}
.forecast-title {color:var(--text);font-size:13px;font-weight:760;}
.forecast-description {color:var(--muted);font-size:11px;margin-top:6px;line-height:1.5;}
.preventive-note {color:#A5D6FF;font-size:12px;margin-top:8px;}
/* Componentes nativos Streamlit. Um tema escuro real, não só cartões escuros. */
.stApp [data-testid="stVerticalBlockBorderWrapper"] > div:has(> [data-testid="stVerticalBlock"]) {border-radius:13px;}
.stApp [data-testid="stMetric"] {
  background:#182D45; border:1px solid var(--border-soft); border-radius:12px;
  padding:11px 12px;
}
.stApp [data-testid="stMetricLabel"] p {color:var(--muted) !important;font-size:12px;}
.stApp [data-testid="stMetricValue"] {color:var(--text) !important;}
.stApp [data-testid="stExpander"] {
  background:#14263D !important;border:1px solid var(--border) !important;
  border-radius:12px !important;overflow:hidden;
}
.stApp [data-testid="stExpander"] summary, .stApp [data-testid="stExpander"] summary p {color:var(--text-soft) !important;}
.stApp [data-testid="stExpander"] summary:hover {background:#1C3450;}
.stApp [data-testid="stForm"] {background:#14263D;border:1px solid var(--border) !important;border-radius:13px;padding:12px;}
/* Botões: padrão deliberadamente claro sobre escuro, sem vazamentos pretos. */
.stApp .stButton button,
.stApp .stFormSubmitButton button,
.stApp .stDownloadButton button,
.stApp [data-testid="stPopover"] > button,
.stApp button[data-testid^="stBaseButton"] {
  background:#1C3550 !important;
  color:#F0F7FF !important;
  border:1px solid #426180 !important;
  border-radius:10px !important;
  box-shadow:none !important;
  font-weight:650 !important;
  min-height:40px;
  transition:background .15s ease,border-color .15s ease;
}
.stApp .stButton button *, .stApp .stFormSubmitButton button *,
.stApp .stDownloadButton button *, .stApp [data-testid="stPopover"] > button *,
.stApp button[data-testid^="stBaseButton"] * {color:inherit !important;}
.stApp .stButton button:hover:not(:disabled),
.stApp .stFormSubmitButton button:hover:not(:disabled),
.stApp .stDownloadButton button:hover:not(:disabled),
.stApp [data-testid="stPopover"] > button:hover:not(:disabled),
.stApp button[data-testid^="stBaseButton"]:hover:not(:disabled) {
  background:#284766 !important;color:#FFFFFF !important;border-color:#76B5ED !important;
}
.stApp .stButton button:focus-visible,
.stApp .stFormSubmitButton button:focus-visible,
.stApp [data-testid="stPopover"] > button:focus-visible {outline:2px solid #8AC9FF; outline-offset:2px;}
.stApp .stButton button:active:not(:disabled),
.stApp .stFormSubmitButton button:active:not(:disabled) {background:#305778 !important;}
.stApp .stButton button[kind="primary"],
.stApp .stFormSubmitButton button[kind="primary"],
.stApp button[data-testid="stBaseButton-primary"] {
  background:#69B5F5 !important;color:#071728 !important;border-color:#69B5F5 !important;
}
.stApp .stButton button[kind="primary"]:hover:not(:disabled),
.stApp .stFormSubmitButton button[kind="primary"]:hover:not(:disabled),
.stApp button[data-testid="stBaseButton-primary"]:hover:not(:disabled) {
  background:#9AD1FF !important;color:#071728 !important;border-color:#9AD1FF !important;
}
.stApp .stButton button:disabled,
.stApp .stFormSubmitButton button:disabled,
.stApp button[data-testid^="stBaseButton"]:disabled {
  background:#17293F !important;color:#7F98B2 !important;border-color:#2A4057 !important;opacity:1 !important;cursor:not-allowed;
}
/* O único popover do sistema é o reinício: aviso discreto de ação destrutiva. */
.stApp [data-testid="stPopover"] > button {
  background:#352738 !important; color:#FFC0CB !important;
  border-color:#815367 !important;
}
.stApp [data-testid="stPopover"] > button:hover:not(:disabled) {
  background:#492E42 !important; color:#FFDBE1 !important;
  border-color:#C17E96 !important;
}
/* Inputs, seletores, popovers e tabelas seguem a mesma paleta. */
.stApp [data-baseweb="input"],
.stApp [data-baseweb="textarea"],
.stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="popover"] {
  background-color:#1A3049 !important;color:var(--text) !important;border-color:#40607C !important;
}
.stApp [data-baseweb="input"] input,
.stApp [data-baseweb="textarea"] textarea,
.stApp [data-baseweb="select"] input,
.stApp [data-baseweb="select"] span {color:var(--text) !important;-webkit-text-fill-color:var(--text) !important;}
.stApp [data-baseweb="input"] input::placeholder,
.stApp [data-baseweb="textarea"] textarea::placeholder {color:#8CA5BF !important;-webkit-text-fill-color:#8CA5BF !important;}
.stApp [data-testid="stNumberInput"] button {background:#1A3049 !important;color:var(--text-soft) !important;border-color:#40607C !important;}
.stApp [data-testid="stSelectbox"] label p,
.stApp [data-testid="stTextInput"] label p,
.stApp [data-testid="stNumberInput"] label p {color:var(--text-soft) !important;font-weight:550;}
.stApp [data-testid="stDataFrame"] {border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.stApp [data-testid="stTabs"] button {color:var(--muted) !important;}
.stApp [data-testid="stTabs"] button[aria-selected="true"] {color:var(--blue) !important;border-bottom-color:var(--blue) !important;}
.stApp [data-testid="stMarkdownContainer"] code {background:#1C3550;color:#C6E5FF;}
/* Acessibilidade e telas menores. */
@media (max-width: 850px) {
  .block-container {padding-left:1.15rem;padding-right:1.15rem;}
  .brand-title {font-size:19px;}
  .logo-frame {width:108px;height:43px;}
  .brand {gap:10px;}
  .clock-time {font-size:23px;}
  .flow-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width: 520px) {
  .header-band {padding:12px;gap:9px;}
  .brand-subtitle {font-size:10px;}
  .brand-title {font-size:17px;}
  .logo-frame {width:85px;height:39px;padding:4px;}
  .logo-oficial {inset:4px;width:calc(100% - 8px);height:calc(100% - 8px);}
  .clock-label {font-size:8px;}
  .clock-time {font-size:20px;}
  .flow-step {padding:11px;}
}
"""
st.markdown("<style>" + CSS_TEMA.replace("__STATE_COLOR__", modo["cor"]).replace("__STATE_SOFT__", modo["leve"]) + "</style>", unsafe_allow_html=True)

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

ICONE_IMPRESSORA = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M6 9V3h12v6M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>'
    '<path d="M6 15h12v6H6zM18 12h.01"/></svg>'
)

st.markdown('<div class="section-name">Impressoras</div>', unsafe_allow_html=True)
colunas_imp = st.columns(2, gap="medium")
for n, coluna in enumerate(colunas_imp, 1):
    imp = sim.impressoras[n]
    estado_imp = sim.status_impressora(n)
    if estado_imp == "STANDBY":
        conteudo = '<div class="printer-doc">Em espera</div><div class="printer-meta">Ativa automaticamente quando a demanda aumenta.</div>'
        situacao = 'STANDBY'
        classe = 'standby'
    elif imp.documento_id is None:
        conteudo = '<div class="printer-doc">Disponível</div><div class="printer-meta">Aguardando próximo pedido</div>'
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
    coluna.markdown(f'<div class="printer-card"><div class="printer-top"><div class="printer-name"><span class="printer-icon">{ICONE_IMPRESSORA}</span> {seguro(nome_imp)}</div>'
                   f'<div class="status {classe}">● {situacao}</div></div>{conteudo}</div>', unsafe_allow_html=True)

area_principal, area_lateral = st.columns([1.75, 1], gap="large")
with area_principal:
    st.markdown(f'<div class="section-name">Fila de espera <span style="color:var(--muted);font-size:13px;font-weight:500">· {len(sim.fila)} documentos</span></div>', unsafe_allow_html=True)
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
