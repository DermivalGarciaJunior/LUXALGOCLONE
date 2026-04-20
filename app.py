import html
from datetime import datetime

import ccxt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# =========================================
# 1. CONFIGURAÇÕES INICIAIS
# =========================================
st.set_page_config(page_title="LuxAlgoClone", layout="wide", page_icon="🏦")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header[data-testid="stHeader"] {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    div[data-testid="stDecoration"] {display: none;}
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 0.5rem;
        max-width: 100%;
    }
    .term-section {
        font-family: ui-monospace, 'Cascadia Code', 'Segoe UI Mono', Consolas, monospace;
        letter-spacing: 0.02em;
        color: #9fe870;
        font-size: 0.78rem;
        text-transform: uppercase;
        margin: 0.35rem 0 0.5rem 0;
        border-bottom: 1px solid #2a3548;
        padding-bottom: 0.25rem;
    }
    .term-title {
        font-family: ui-monospace, 'Cascadia Code', Consolas, monospace;
        font-size: 1.35rem;
        font-weight: 700;
        color: #e8edf5;
        margin: 0 0 0.75rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-family: ui-monospace, Consolas, monospace;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================
# 2. INICIALIZAÇÃO DA MEMÓRIA
# =========================================
def inicializar_estado() -> None:
    defaults = {
        "banca": 1000.0,
        "banca_inicial_dia": 1000.0,
        "data_referencia": datetime.now().date(),
        "em_operacao": False,
        "logs": [],
        "ultimo_preco": 0.0,
        "kill_switch_ativo": False,
        "hora_inicio_bot": datetime.now(),
        "tipo_op": "",
        "preco_entrada": 0.0,
        "ob_bullish": None,
        "ob_bearish": None,
    }

    for chave, valor in defaults.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor


inicializar_estado()


# Reset diário
data_hoje = datetime.now().date()
if st.session_state.data_referencia != data_hoje:
    st.session_state.data_referencia = data_hoje
    st.session_state.banca_inicial_dia = st.session_state.banca
    st.session_state.kill_switch_ativo = False
    st.session_state.hora_inicio_bot = datetime.now()
    st.session_state.logs.append(f"📅 Novo dia: {data_hoje}. Limites resetados.")


# =========================================
# 3. CONEXÃO E DADOS
# =========================================
@st.cache_data(ttl=30, show_spinner=False)
def buscar_dados() -> pd.DataFrame:
    """
    Busca dados públicos da Binance.
    Para OHLCV público, não é necessário usar API key.
    """
    exchange = ccxt.binance({
        "enableRateLimit": True,
        "timeout": 15000,
    })

    bars = exchange.fetch_ohlcv("AVAX/USDT", timeframe="15m", limit=200)

    if not bars:
        raise RuntimeError("A Binance retornou uma lista vazia de candles.")

    df = pd.DataFrame(
        bars,
        columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Lógica Smart Money: swing highs/lows
    window = 5
    df["swing_high"] = df["high"].rolling(window=window, center=True).max()
    df["swing_low"] = df["low"].rolling(window=window, center=True).min()

    df["last_swing_high"] = df["swing_high"].ffill()
    df["last_swing_low"] = df["swing_low"].ffill()

    # Break of Structure
    df["bos_bullish"] = df["close"] > df["last_swing_high"].shift(1)
    df["bos_bearish"] = df["close"] < df["last_swing_low"].shift(1)

    df["vol_media"] = df["volume"].rolling(window=10).mean()

    return df


# =========================================
# 4. FUNÇÕES AUXILIARES
# =========================================
def _render_log_entry(texto: str) -> None:
    t = texto.upper()
    if "COMPRA" in t or "LONG" in t or "🟢" in texto:
        st.success(texto)
    elif "VENDA" in t or "SHORT" in t or "🔴" in texto:
        st.error(texto)
    elif "🏁" in texto:
        st.info(texto)
    elif "📅" in texto:
        st.warning(texto)
    else:
        st.caption(texto)


def metrica_dinamica(label: str, valor: str, meta_batida: bool, subtexto: str = "") -> None:
    cor = "#00C07F" if meta_batida else "#FF4B4B"
    label_e = html.escape(label)
    valor_e = html.escape(valor)

    sub_html = ""
    if subtexto:
        sub_html = (
            f'<div style="font-size:0.75rem;color:#8b9cb3;margin-top:0.35rem;line-height:1.3;">'
            f"{html.escape(subtexto)}</div>"
        )

    st.markdown(
        f"""
        <div style="font-family:ui-monospace,'Cascadia Code','Segoe UI Mono',Consolas,monospace;padding:0.2rem 0;">
            <div style="font-size:0.78rem;color:#8b9cb3;margin-bottom:0.3rem;">{label_e}</div>
            <div style="font-size:1.45rem;font-weight:600;color:{cor};line-height:1.15;">{valor_e}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# 5. CABEÇALHO E CONTROLES
# =========================================
st.markdown('<p class="term-title">LuxAlgoClone · AVAX/USDT · 15m</p>', unsafe_allow_html=True)

col_a, col_b = st.columns([1, 4])
with col_a:
    atualizar = st.button("🔄 Atualizar dados", use_container_width=True)
with col_b:
    st.caption("Clique em atualizar para buscar candles novos da Binance.")

if atualizar:
    buscar_dados.clear()


# =========================================
# 6. BUSCA DOS DADOS COM TRATAMENTO CORRETO
# =========================================
try:
    df = buscar_dados()
except Exception as e:
    st.error(f"Erro ao buscar dados da Binance: {e}")
    st.info("Verifique a conexão, tente atualizar novamente e confirme se a Binance está acessível no servidor.")
    st.stop()


# =========================================
# 7. VARIÁVEIS DE MERCADO
# =========================================
preco_atual = float(df["close"].iloc[-1])
vol_atual = float(df["volume"].iloc[-1])
vol_media = float(df["vol_media"].iloc[-1]) if pd.notna(df["vol_media"].iloc[-1]) else 0.0

perda_dia = (
    (st.session_state.banca - st.session_state.banca_inicial_dia)
    / st.session_state.banca_inicial_dia
)

if perda_dia <= -0.03:
    st.session_state.kill_switch_ativo = True


# =========================================
# 8. DETECÇÃO DE ORDER BLOCKS E TRADING
# =========================================
recent_bos_bull = bool(df["bos_bullish"].iloc[-4:-1].any())
recent_bos_bear = bool(df["bos_bearish"].iloc[-4:-1].any())

# Salva a zona do Order Block quando ocorre um BOS
if recent_bos_bull:
    min_low_idx = df["low"].iloc[-10:-1].idxmin()
    st.session_state.ob_bullish = {
        "high": float(df.loc[min_low_idx, "high"]),
        "low": float(df.loc[min_low_idx, "low"]),
        "time": df.loc[min_low_idx, "timestamp"],
    }

if recent_bos_bear:
    max_high_idx = df["high"].iloc[-10:-1].idxmax()
    st.session_state.ob_bearish = {
        "high": float(df.loc[max_high_idx, "high"]),
        "low": float(df.loc[max_high_idx, "low"]),
        "time": df.loc[max_high_idx, "timestamp"],
    }

# Gatilho: operar na mitigação do Order Block
if not st.session_state.kill_switch_ativo and not st.session_state.em_operacao:
    if st.session_state.ob_bullish is not None:
        ob = st.session_state.ob_bullish
        if ob["low"] <= preco_atual <= (ob["high"] * 1.002) and vol_atual > vol_media:
            st.session_state.em_operacao = True
            st.session_state.tipo_op = "LONG"
            st.session_state.preco_entrada = preco_atual
            st.session_state.logs.append(
                f"🟢 MITIGAÇÃO LONG: Ordem Institucional @ ${preco_atual:,.2f}"
            )
            st.session_state.ob_bullish = None

    elif st.session_state.ob_bearish is not None:
        ob = st.session_state.ob_bearish
        if (ob["low"] * 0.998) <= preco_atual <= ob["high"] and vol_atual > vol_media:
            st.session_state.em_operacao = True
            st.session_state.tipo_op = "SHORT"
            st.session_state.preco_entrada = preco_atual
            st.session_state.logs.append(
                f"🔴 MITIGAÇÃO SHORT: Ordem Institucional @ ${preco_atual:,.2f}"
            )
            st.session_state.ob_bearish = None


# =========================================
# 9. GESTÃO DE SAÍDA
# =========================================
if st.session_state.em_operacao:
    entrada = st.session_state.preco_entrada
    lucro_alvo = 0.012
    stop_loss = 0.006

    if st.session_state.tipo_op == "LONG":
        variacao = (preco_atual - entrada) / entrada
    else:
        variacao = (entrada - preco_atual) / entrada

    if variacao >= lucro_alvo or variacao <= -stop_loss:
        resultado = st.session_state.banca * variacao
        st.session_state.banca += resultado
        st.session_state.em_operacao = False

        motivo = "ALVO ATINGIDO" if variacao >= lucro_alvo else "STOP LOSS"
        st.session_state.logs.append(
            f"🏁 {motivo} | Result: ${resultado:.2f} ({variacao * 100:.2f}%)"
        )


# =========================================
# 10. TAXÍMETRO DE RENDIMENTO
# =========================================
_inicio = st.session_state.hora_inicio_bot
tempo_online = (datetime.now() - _inicio).total_seconds() if isinstance(_inicio, datetime) else 0.0
lucro_atual = st.session_state.banca - st.session_state.banca_inicial_dia

if tempo_online >= 60:
    lucro_por_hora = lucro_atual * 3600.0 / tempo_online
    banca_ini = st.session_state.banca_inicial_dia
    pct_por_hora = (lucro_por_hora / banca_ini * 100.0) if banca_ini else 0.0
else:
    lucro_por_hora = 0.0
    pct_por_hora = 0.0

horas_rodando = int(tempo_online // 3600)
minutos_rodando = int((tempo_online % 3600) // 60)


# =========================================
# 11. INTERFACE
# =========================================
st.markdown('<p class="term-section">Visão Geral Institucional</p>', unsafe_allow_html=True)
f1, f2, f3, f4, f5 = st.columns(5)

delta_banca = st.session_state.banca - st.session_state.banca_inicial_dia
meta_saldo = delta_banca > 0

with f1:
    metrica_dinamica(
        "Saldo",
        f"${st.session_state.banca:,.2f}",
        meta_saldo,
        f"P/L dia: {delta_banca:+,.2f}",
    )

with f2:
    if st.session_state.em_operacao:
        tipo = st.session_state.tipo_op
        ent = st.session_state.preco_entrada
        metrica_dinamica("Posição", tipo, True, f"@{ent:,.2f}")
    else:
        metrica_dinamica("Posição", "FLAT", False, "—")

with f3:
    if st.session_state.kill_switch_ativo:
        metrica_dinamica("Status", "KILL SWITCH", False, "Trading off")
    else:
        metrica_dinamica("Status", "ARMADO", True, "Buscando Mitigação")

with f4:
    metrica_dinamica(
        "Risco/Retorno",
        "1:2 (SMC)",
        not st.session_state.kill_switch_ativo,
        "TP 1.2% / SL 0.6%",
    )

with f5:
    meta_taxa = lucro_atual > 0
    metrica_dinamica(
        f"Taxa de Rendimento (Uptime: {horas_rodando}h {minutos_rodando}m)",
        f"${lucro_por_hora:,.2f} / h",
        meta_taxa,
        f"{pct_por_hora:+.2f}% por hora",
    )


st.markdown('<p class="term-section">Telemetria Smart Money</p>', unsafe_allow_html=True)
t1, t2, t3, t4, t5 = st.columns(5)

delta_preco = (
    preco_atual - st.session_state.ultimo_preco
    if st.session_state.ultimo_preco != 0
    else 0.0
)
st.session_state.ultimo_preco = preco_atual

zonas_ativas = sum([
    st.session_state.ob_bullish is not None,
    st.session_state.ob_bearish is not None,
])

vol_ok = vol_media > 0 and vol_atual > vol_media
rel = (vol_atual / vol_media) if vol_media > 0 else 0.0

with t1:
    metrica_dinamica("Preço", f"${preco_atual:,.2f}", delta_preco > 0, f"Δ {delta_preco:+,.2f}")

with t2:
    if recent_bos_bull:
        metrica_dinamica("Estrutura (BOS)", "BULLISH", True, "Rompimento de Topo")
    elif recent_bos_bear:
        metrica_dinamica("Estrutura (BOS)", "BEARISH", True, "Rompimento de Fundo")
    else:
        metrica_dinamica("Estrutura (BOS)", "CONSOLIDAÇÃO", False, "Aguardando ChoCh")

with t3:
    metrica_dinamica("Zonas Ativas (OB)", f"{zonas_ativas}", zonas_ativas > 0, "Demand/Supply")

with t4:
    metrica_dinamica("Força Institucional", f"{vol_atual:,.0f}", vol_ok, f"{rel:.2f}× média")

with t5:
    if st.session_state.em_operacao:
        metrica_dinamica("Ação Bot", "EM OPERAÇÃO", True, st.session_state.tipo_op)
    else:
        metrica_dinamica("Ação Bot", "RASTREAMENTO", False, "Monitorando Zonas")


# =========================================
# 12. GRÁFICO E LOGS
# =========================================
st.markdown('<p class="term-section">Mesa de Operações (Order Blocks)</p>', unsafe_allow_html=True)
mesa_graf, mesa_log = st.columns([3, 1])

fig = go.Figure(
    data=[
        go.Candlestick(
            x=df["timestamp"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name="AVAX",
        )
    ]
)

# Order Block de compra
if st.session_state.ob_bullish is not None:
    ob = st.session_state.ob_bullish
    fig.add_shape(
        type="rect",
        x0=ob["time"],
        y0=ob["low"],
        x1=df["timestamp"].iloc[-1],
        y1=ob["high"],
        fillcolor="rgba(0, 255, 0, 0.15)",
        line=dict(color="rgba(0, 255, 0, 0.6)", width=1),
        layer="below",
    )

# Order Block de venda
if st.session_state.ob_bearish is not None:
    ob = st.session_state.ob_bearish
    fig.add_shape(
        type="rect",
        x0=ob["time"],
        y0=ob["low"],
        x1=df["timestamp"].iloc[-1],
        y1=ob["high"],
        fillcolor="rgba(255, 0, 0, 0.15)",
        line=dict(color="rgba(255, 0, 0, 0.6)", width=1),
        layer="below",
    )

fig.update_layout(
    template="plotly_dark",
    xaxis_rangeslider_visible=False,
    margin=dict(l=0, r=0, t=36, b=0),
    height=480,
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font=dict(color="#c9d1d9"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

with mesa_graf:
    st.plotly_chart(fig, use_container_width=True)

with mesa_log:
    st.markdown("**Feed de Mitigação**")
    for log in reversed(st.session_state.logs[-15:]):
        _render_log_entry(log)


# =========================================
# 13. RODAPÉ
# =========================================
st.caption("Aplicativo carregado. Use o botão 'Atualizar dados' para buscar candles novos.")
