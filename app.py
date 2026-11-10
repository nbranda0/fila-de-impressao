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
    # Não misturar texto de fallback e imagem na mesma área: a sobreposição
    # deixava a logo ilegível no navegador publicado.
    return f'<img class="logo-oficial" alt="UNIFACS" src="{src}">'


if "simulador" not in st.session_state:
    st.session_state.simulador = SimuladorImpressao()
sim: SimuladorImpressao = st.session_state.simulador
modo = ESTILOS[sim.estado]
texto_estado = ("A impressora 2 foi ativada preventivamente para reduzir o risco de atraso."
                if sim.estado == "NORMAL" and sim._apoio_preventivo else modo["texto"])

# CSS isolado da lógica: paleta escura coerente para todos os componentes.
CSS_TEMA = r"""
/* Fila de Impressão — visual azul-noturno v1.3
   O tema nativo fica em .streamlit/config.toml; este CSS estiliza
   o dashboard e poucos controles específicos. */
:root {
  color-scheme: dark;
  --bg: #0A1424;
  --surface: #142640;
  --surface-raised: #192E49;
  --border: #2E4967;
  --border-soft: #263F5D;
  --text: #F1F7FF;
  --text-soft: #D0DEEF;
  --muted: #AEC0D6;
  --dim: #99ADC5;
  --blue: #89C7FF;
  --blue-strong: #5EAEF6;
  --green: #78E1C2;
  --orange: #F7BF75;
  --red: #FF97A7;
  --state: __STATE_COLOR__;
  --state-soft: __STATE_SOFT__;
}
html, body, [data-testid="stAppViewContainer"], .stApp {
  background: var(--bg) !important;
  color: var(--text);
}
.stApp {
  background-image: radial-gradient(ellipse 960px 430px at 30% -180px, #1C3553 0%, #0A1424 76%) !important;
}
/* A barra administrativa do Community Cloud fica sobre o canto superior direito.
   Mantemos folga em cima para ela não cobrir o relógio. */
.block-container {max-width: 1280px; padding: 3.6rem 1.75rem 3.2rem !important;}
#MainMenu, footer {visibility: hidden;}
header[data-testid="stHeader"] {background:transparent !important;}
section[data-testid="stSidebar"] {background:#0E1D32 !important;}
.stApp h1, .stApp h2, .stApp h3 {color:var(--text);}
.stApp a {color:var(--blue);}
.stApp a:hover {color:#C1E4FF;}
.stApp hr {border-color:var(--border-soft);}

/* Marca, relógio e banner operacional */
.header-band {
  display:flex; align-items:center; justify-content:space-between; gap:24px;
  padding:17px 21px; border-radius:16px;
  background:linear-gradient(110deg, #192F4B 0%, #14253D 84%);
  border:1px solid #345270; box-shadow:0 12px 28px rgba(0,8,22,.16);
  margin:0 0 14px;
}
.brand {display:flex; align-items:center;gap:17px;min-width:0;}
.logo-frame {
  width:155px;height:58px;display:flex;align-items:center;justify-content:center;
  padding:7px 13px; border-radius:11px;background:#FFFFFF;flex-shrink:0;
}
.logo-oficial {display:block;object-fit:contain;width:100%;max-height:44px;}
.brand-title {font-size:25px;font-weight:790;line-height:1.12;letter-spacing:-.035em;color:var(--text);}
.brand-subtitle {font-size:13px;color:var(--muted);margin-top:6px;line-height:1.3;}
.clock {text-align:right;flex-shrink:0;min-width:130px;}
.clock-label {font-size:11px;color:var(--muted);letter-spacing:.04em;text-transform:uppercase;}
.clock-time {font-size:31px;font-weight:800;line-height:1.06;letter-spacing:-.025em;margin-top:5px;color:#EFF8FF;font-variant-numeric:tabular-nums;}
.state-panel {
  border-radius:12px;padding:13px 17px;margin:1px 0 17px;
  background:linear-gradient(110deg,var(--state-soft),#13243A 88%);
  border:1px solid #3A536E;border-left:4px solid var(--state);
}
.state-name {font-size:16px;font-weight:760;color:var(--state);line-height:1.35;}
.state-desc {font-size:13px;line-height:1.55;color:var(--text-soft);margin-top:4px;}

/* Títulos e indicadores de fluxo */
.section-name {font-size:19px;line-height:1.35;font-weight:780;letter-spacing:-.02em;color:var(--text);margin:18px 0 10px;}
.section-sub {font-size:13px;color:var(--muted);margin:0 0 12px;line-height:1.5;}
.flow-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;margin:13px 0 22px;}
.flow-step {position:relative;overflow:hidden;border-radius:13px;border:1px solid var(--border-soft);background:linear-gradient(145deg,#182E48,#14253D);padding:17px 18px;}
.flow-step::before {content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--state);opacity:.8;}
.flow-step strong {display:block;color:var(--text);font-size:29px;font-weight:780;line-height:1.12;font-variant-numeric:tabular-nums;}
.flow-step span {display:block;color:var(--muted);font-size:13px;margin-top:7px;}

/* Impressoras: compactas quando inativas, com progresso quando ocupadas */
.printer-card {box-sizing:border-box;min-height:152px;background:linear-gradient(150deg,#1B314B,#14253D);border:1px solid var(--border);border-top:3px solid var(--state);border-radius:15px;padding:17px 18px;margin:3px 0 5px;}
.printer-card.standby-card {min-height:152px;background:linear-gradient(150deg,#15283F,#122238);border-color:#2A435F;border-top-color:#455C77;}
.printer-top {display:flex;justify-content:space-between;align-items:center;gap:10px;}
.printer-name {display:flex;align-items:center;gap:9px;font-size:16px;font-weight:770;color:var(--text);}
.printer-icon {display:inline-flex;color:var(--blue);align-items:center;}
.printer-icon svg {width:21px;height:21px;}
.status {font-size:11px;color:var(--muted);font-weight:750;letter-spacing:.04em;white-space:nowrap;}
.status.printing {color:var(--green);}
.status.standby {color:var(--dim);}
.printer-doc {font-size:16px;font-weight:720;color:var(--text);margin-top:17px;margin-bottom:5px;overflow-wrap:anywhere;line-height:1.38;}
.printer-meta {font-size:13px;color:var(--muted);margin-top:5px;line-height:1.45;}
.printer-reason {font-size:12px;color:var(--dim);margin-top:9px;line-height:1.45;}
.progress-track {width:100%;height:8px;background:#091A2C;border:1px solid #315171;border-radius:999px;margin-top:12px;overflow:hidden;}
.progress-fill {height:100%;background:linear-gradient(90deg,#4C9AE6,#95D2FF);border-radius:999px;transition:width .18s ease;}

/* Fila: cartões legíveis sem aparência de planilha */
.job-card {background:linear-gradient(130deg,#1A304B,#15283F);border:1px solid var(--border-soft);border-left:4px solid #78BEFC;border-radius:12px;padding:13px 15px;margin:0 0 8px;}
.job-card.urgent {border-left-color:var(--orange);}
.job-card.overdue {border-left-color:var(--red);background:#29283E;}
.job-top {display:flex;align-items:center;justify-content:space-between;gap:10px;}
.job-title {color:var(--text);font-size:15px;font-weight:740;overflow-wrap:anywhere;line-height:1.4;}
.job-meta {color:var(--muted);font-size:13px;margin-top:6px;line-height:1.55;}
.job-tag {color:#C1E2FF;background:#213E5C;border:1px solid #365C7F;border-radius:99px;padding:4px 9px;font-size:11px;font-weight:700;white-space:nowrap;}
.job-tag.urgent {color:#FFE0B5;background:#48341F;border-color:#80592F;}
.job-tag.overdue {color:#FFD1D8;background:#4E2D3C;border-color:#915063;}
.number {color:#8BC7FF;font-weight:850;margin-right:11px;font-variant-numeric:tabular-nums;}
.empty-card {background:#11243A;border:1px dashed #385777;border-radius:12px;padding:24px 18px;color:var(--muted);text-align:center;font-size:14px;line-height:1.6;}
.small-note {color:var(--muted);font-size:13px;margin:10px 0 14px;line-height:1.55;}
.done-card {background:linear-gradient(135deg,#192D46,#14263D);border:1px solid var(--border-soft);border-left:3px solid var(--green);border-radius:12px;padding:14px 16px;margin:5px 0 10px;min-height:102px;}
.done-title {color:var(--text);font-size:15px;font-weight:740;line-height:1.4;overflow-wrap:anywhere;}
.done-meta {color:var(--muted);font-size:13px;margin-top:6px;line-height:1.5;}
.done-bad {color:var(--red);}
.done-good {color:var(--green);}
.forecast-box {background:#182C44;border:1px solid var(--border-soft);border-radius:12px;padding:14px 15px;margin:11px 0;}
.forecast-box.risk {border-left:3px solid var(--orange);}
.forecast-box.safe {border-left:3px solid var(--green);}
.forecast-title {color:var(--text);font-size:14px;font-weight:730;line-height:1.4;}
.forecast-description {color:var(--muted);font-size:13px;margin-top:6px;line-height:1.55;}
.preventive-note {color:#B5DDFF;font-size:13px;margin-top:9px;}

/* Estilo dos componentes nativos do Streamlit: manter o tom escuro.
   Usar as configurações do tema para tipografia base; CSS apenas onde necessário. */
.stApp [data-testid="stMetric"] {background:#182D45;border:1px solid var(--border-soft);border-radius:12px;padding:14px 15px;}
.stApp [data-testid="stMetricLabel"] p {color:var(--muted) !important;font-size:13px;}
.stApp [data-testid="stMetricValue"] {color:var(--text) !important;}
.stApp [data-testid="stExpander"] {background:#14263D !important;border:1px solid var(--border) !important;border-radius:12px !important;overflow:hidden;}
.stApp [data-testid="stExpander"] summary, .stApp [data-testid="stExpander"] summary p {color:var(--text-soft) !important;font-size:14px;}
.stApp [data-testid="stExpander"] summary:hover {background:#213953;}
.stApp [data-testid="stForm"] {background:#14263D;border:1px solid var(--border) !important;border-radius:13px;padding:15px;}
.stApp [data-testid="stWidgetLabel"] p {font-size:14px;color:var(--text-soft) !important;}

/* Botões: contraste legível nos estados normal, hover, disabled e primary */
.stApp .stButton button,
.stApp .stFormSubmitButton button,
.stApp .stDownloadButton button,
.stApp [data-testid="stPopover"] > button,
.stApp button[data-testid^="stBaseButton"] {
  background:#213D5A !important;
  color:#F3F8FE !important;
  border:1px solid #46698B !important;
  border-radius:10px !important;
  box-shadow:none !important;
  font-size:14px !important;
  font-weight:660 !important;
  min-height:43px;
  transition:background .16s ease,border-color .16s ease;
}
.stApp .stButton button *, .stApp .stFormSubmitButton button *,
.stApp .stDownloadButton button *, .stApp [data-testid="stPopover"] > button *,
.stApp button[data-testid^="stBaseButton"] * {color:inherit !important;}
.stApp .stButton button:hover:not(:disabled), .stApp .stFormSubmitButton button:hover:not(:disabled),
.stApp .stDownloadButton button:hover:not(:disabled), .stApp [data-testid="stPopover"] > button:hover:not(:disabled),
.stApp button[data-testid^="stBaseButton"]:hover:not(:disabled) {
  background:#2B5278 !important;color:#FFF !important;border-color:#86C6FF !important;
}
.stApp .stButton button:focus-visible,
.stApp .stFormSubmitButton button:focus-visible,
.stApp [data-testid="stPopover"] > button:focus-visible {outline:2px solid #9AD2FF;outline-offset:2px;}
.stApp .stButton button[kind="primary"],
.stApp .stFormSubmitButton button[kind="primary"],
.stApp button[data-testid="stBaseButton-primary"] {background:#7ABDF6 !important;color:#07192B !important;border-color:#7ABDF6 !important;}
.stApp .stButton button[kind="primary"]:hover:not(:disabled),
.stApp .stFormSubmitButton button[kind="primary"]:hover:not(:disabled),
.stApp button[data-testid="stBaseButton-primary"]:hover:not(:disabled) {background:#A9DBFF !important;color:#07192B !important;border-color:#A9DBFF !important;}
.stApp .stButton button:disabled,.stApp .stFormSubmitButton button:disabled,
.stApp button[data-testid^="stBaseButton"]:disabled {background:#172B43 !important;color:#8DA4BD !important;border-color:#304A65 !important;opacity:1 !important;}
.stApp [data-testid="stPopover"] > button {background:#3B2B39 !important;color:#FFD4DF !important;border-color:#875C70 !important;}
.stApp [data-testid="stPopover"] > button:hover:not(:disabled) {background:#57384C !important;color:#FFE4EC !important;border-color:#C787A3 !important;}

/* Inputs: impede o tom amarronzado observado nos prints do deploy. */
.stApp [data-baseweb="input"],
.stApp [data-baseweb="input"] > div,
.stApp [data-baseweb="textarea"],
.stApp [data-baseweb="select"] > div,
.stApp [data-testid="stTextInput"] input,
.stApp [data-testid="stNumberInput"] input,
.stApp [data-baseweb="popover"] {
  background:#1B3551 !important;color:var(--text) !important;border-color:#4A6D90 !important;
}
.stApp [data-baseweb="input"] input,
.stApp [data-baseweb="textarea"] textarea,
.stApp [data-baseweb="select"] input,
.stApp [data-baseweb="select"] span,
.stApp [data-testid="stNumberInput"] input {color:var(--text) !important;-webkit-text-fill-color:var(--text) !important;}
.stApp [data-baseweb="input"] input::placeholder,
.stApp [data-baseweb="textarea"] textarea::placeholder {color:#AFBED0 !important;-webkit-text-fill-color:#AFBED0 !important;}
.stApp [data-testid="stNumberInput"] button {background:#254361 !important;color:var(--text) !important;border-color:#4A6D90 !important;}
.stApp [data-testid="stDataFrame"] {border:1px solid var(--border);border-radius:10px;overflow:hidden;}
.stApp [data-testid="stTabs"] button {color:var(--muted) !important;}
.stApp [data-testid="stTabs"] button[aria-selected="true"] {color:var(--blue) !important;border-bottom-color:var(--blue) !important;}
.stApp [data-testid="stMarkdownContainer"] code {background:#223F5B;color:#D2E9FF;}
@media (max-width: 920px) {
  .block-container {padding:3.6rem 1.25rem 2.5rem !important;}
  .flow-grid {grid-template-columns:repeat(2,minmax(0,1fr));}
}
@media (max-width: 640px) {
  .block-container {padding:3.4rem .85rem 2rem !important;}
  .header-band {flex-wrap:wrap;padding:14px;gap:12px;}
  .brand {gap:10px;}
  .logo-frame {width:112px;height:46px;padding:5px 8px;}
  .logo-oficial {max-height:36px;}
  .brand-title {font-size:20px;}
  .brand-subtitle {font-size:12px;}
  .clock {text-align:left;min-width:0;}
  .clock-time {font-size:26px;}
  .flow-step {padding:14px;}
  .flow-step strong {font-size:25px;}
  .job-title {font-size:14px;}
  .job-meta {font-size:12px;}
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
        conteudo = '<div class="printer-doc">Em espera</div><div class="printer-meta">Ativação automática conforme a demanda.</div>'
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
    coluna.markdown(f'<div class="printer-card {"standby-card" if estado_imp == "STANDBY" else ""}"><div class="printer-top"><div class="printer-name"><span class="printer-icon">{ICONE_IMPRESSORA}</span> {seguro(nome_imp)}</div>'
                   f'<div class="status {classe}">● {situacao}</div></div>{conteudo}</div>', unsafe_allow_html=True)

area_principal, area_lateral = st.columns([1.75, 1], gap="large")
with area_principal:
    st.markdown(f'<div class="section-name">Fila de espera <span style="color:var(--muted);font-size:13px;font-weight:500">· {len(sim.fila)} documentos</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Maior prioridade → menos páginas → chegada mais antiga → ID</div>', unsafe_allow_html=True)
    fila_container = st.container(height=420, border=False) if len(sim.fila) > 6 else st.container(border=False)
    with fila_container:
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
    agendados_container = (st.container(height=250, border=False)
                           if len(sim.documentos_agendados()) > 4 else st.container(border=False))
    with agendados_container:
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
