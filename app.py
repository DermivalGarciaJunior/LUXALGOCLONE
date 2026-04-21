import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LuxAlgoClone", layout="wide", page_icon="📈")


# =========================================
# CONFIGURAÇÕES
# =========================================
REFRESH_MINUTOS = 1
REFRESH_MS = REFRESH_MINUTOS * 60 * 1000
MAX_RSI_LOGS = 60
MAX_LOGS = 200


# =========================================
# ESTILO
# =========================================
st.markdown(
    """
    <style>
    .top-card {
        background: #07111f;
        border-radius: 10px;
        padding: 18px 18px 10px 18px;
        margin-bottom: 16px;
    }

    .top-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: white;
        margin-bottom: 8px;
    }

    .top-subtitle {
        font-size: 0.95rem;
        color: #b7c2d0;
        margin-bottom: 18px;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #c3cede;
        margin-bottom: 4px;
    }

    .metric-value {
        font-size: 1.05rem;
        font-weight: 700;
        color: white;
    }

    .col-title {
        display: inline-block;
        background: #000000;
        color: white;
        font-weight: 800;
        font-size: 1.02rem;
        padding: 2px 8px;
        border-radius: 2px;
        margin-bottom: 8px;
    }

    .plain-title {
        color: white;
        font-weight: 700;
        font-size: 1.02rem;
        margin-bottom: 8px;
    }

    .data-box {
        background: #e9e9e9;
        border-radius: 4px;
        min-height: 320px;
        padding: 12px;
        color: #111111;
    }

    .data-list {
        font-size: 1rem;
        line-height: 1.6;
        font-weight: 600;
        white-space: pre-wrap;
        color: #111111;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================
# ESTADO
# =========================================
def inicializar_estado() -> None:
    if "token_input_widget" not in st.session_state:
        st.session_state.token_input_widget = "AVAX"

    if "token_confirmado" not in st.session_state:
        st.session_state.token_confirmado = "AVAX"

    if "monitor_ativo" not in st.session_state:
        st.session_state.monitor_ativo = False

    if "ultimo_preco" not in st.session_state:
        st.session_state.ultimo_preco = None

    if "erro_tela" not in st.session_state:
        st.session_state.erro_tela = ""

    if "rsi_15m" not in st.session_state:
        st.session_state.rsi_15m = None

    if "rsi_4h" not in st.session_state:
        st.session_state.rsi_4h = None

    if "rsi_1w" not in st.session_state:
        st.session_state.rsi_1w = None

    if "ema_20" not in st.session_state:
        st.session_state.ema_20 = None

    if "ema_50" not in st.session_state:
        st.session_state.ema_50 = None

    if "ema_200" not in st.session_state:
        st.session_state.ema_200 = None

    if "logs_datahora" not in st.session_state:
        st.session_state.logs_datahora = []

    if "logs_preco" not in st.session_state:
        st.session_state.logs_preco = []

    if "rsi_logs_15m" not in st.session_state:
        st.session_state.rsi_logs_15m = []

    if "rsi_logs_4h" not in st.session_state:
        st.session_state.rsi_logs_4h = []

    if "rsi_logs_1w" not in st.session_state:
        st.session_state.rsi_logs_1w = []

    if "logs_bot" not in st.session_state:
        st.session_state.logs_bot = []


inicializar_estado()


# =========================================
# AUTO REFRESH
# =========================================
if st.session_state.monitor_ativo:
    contador_refresh = st_autorefresh(interval=REFRESH_MS, key="refresh_1min")
else:
    contador_refresh = 0


# =========================================
# FUNÇÕES
# =========================================
def limpar_dados_visuais() -> None:
    st.session_state.ultimo_preco = None
    st.session_state.erro_tela = ""
    st.session_state.rsi_15m = None
    st.session_state.rsi_4h = None
    st.session_state.rsi_1w = None
    st.session_state.ema_20 = None
    st.session_state.ema_50 = None
    st.session_state.ema_200 = None
    st.session_state.logs_datahora = []
    st.session_state.logs_preco = []
    st.session_state.rsi_logs_15m = []
    st.session_state.rsi_logs_4h = []
    st.session_state.rsi_logs_1w = []
    st.session_state.logs_bot = []


def buscar_preco_okx(token: str) -> float:
    simbolo = f"{token}-USDT"
    url = "https://www.okx.com/api/v5/market/ticker"
    params = {"instId": simbolo}

    resposta = requests.get(url, params=params, timeout=20)
    resposta.raise_for_status()
    dados = resposta.json()

    if dados.get("code") != "0":
        raise Exception(f"Falha na OKX: {dados}")

    lista = dados.get("data", [])
    if not lista:
        raise Exception(f"Token {token} não encontrado em par USDT na OKX.")

    ultimo = lista[0].get("last")
    if ultimo is None:
        raise Exception(f"Preço não retornado para {token}/USDT.")

    return float(ultimo)


def buscar_candles_okx(token: str, bar: str, limit: int = 300) -> pd.DataFrame:
    simbolo = f"{token}-USDT"
    url = "https://www.okx.com/api/v5/market/candles"
    params = {
        "instId": simbolo,
        "bar": bar,
        "limit": str(limit),
    }

    resposta = requests.get(url, params=params, timeout=20)
    resposta.raise_for_status()
    dados = resposta.json()

    if dados.get("code") != "0":
        raise Exception(f"Falha ao buscar candles {bar}: {dados}")

    lista = dados.get("data", [])
    if not lista:
        raise Exception(f"Sem candles para {token}/USDT em {bar}.")

    df = pd.DataFrame(
        lista,
        columns=[
            "ts", "open", "high", "low", "close", "vol",
            "volCcy", "volCcyQuote", "confirm"
        ],
    )

    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["ts"] = pd.to_datetime(pd.to_numeric(df["ts"]), unit="ms")
    df = df.sort_values("ts").reset_index(drop=True)
    return df


def calcular_rsi(series: pd.Series, periodo: int = 14) -> float | None:
    series = pd.to_numeric(series, errors="coerce").dropna()

    if len(series) < periodo + 1:
        return None

    delta = series.diff()
    ganho = delta.clip(lower=0)
    perda = -delta.clip(upper=0)

    media_ganho = ganho.ewm(alpha=1 / periodo, adjust=False).mean()
    media_perda = perda.ewm(alpha=1 / periodo, adjust=False).mean()

    rs = media_ganho / media_perda.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    ultimo = rsi.iloc[-1]

    if pd.isna(ultimo):
        return None

    return float(ultimo)


def calcular_ema(series: pd.Series, periodo: int) -> float | None:
    series = pd.to_numeric(series, errors="coerce").dropna()
    if len(series) < periodo:
        return None
    ema = series.ewm(span=periodo, adjust=False).mean()
    ultimo = ema.iloc[-1]
    if pd.isna(ultimo):
        return None
    return float(ultimo)


def registrar_linha(lista_nome: str, texto: str) -> None:
    lista = st.session_state[lista_nome]
    if not lista or lista[0] != texto:
        lista.insert(0, texto)
        st.session_state[lista_nome] = lista[:MAX_RSI_LOGS]


def registrar_log_simples(token: str, preco: float) -> None:
    horario_completo = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    novo = {
        "Horário": horario_completo,
        "Token": token,
        "Preço": round(preco, 6),
    }

    if st.session_state.logs_bot:
        ultimo = st.session_state.logs_bot[0]
        if (
            ultimo["Horário"] == novo["Horário"]
            and ultimo["Token"] == novo["Token"]
            and ultimo["Preço"] == novo["Preço"]
        ):
            return

    st.session_state.logs_bot.insert(0, novo)
    st.session_state.logs_bot = st.session_state.logs_bot[:MAX_LOGS]


def atualizar_tela(token: str) -> None:
    preco = buscar_preco_okx(token)

    df_15m = buscar_candles_okx(token, "15m", 300)
    df_4h = buscar_candles_okx(token, "4H", 300)
    df_1w = buscar_candles_okx(token, "1W", 300)

    rsi_15m = calcular_rsi(df_15m["close"], 14)
    rsi_4h = calcular_rsi(df_4h["close"], 14)
    rsi_1w = calcular_rsi(df_1w["close"], 14)

    ema_20 = calcular_ema(df_15m["close"], 20)
    ema_50 = calcular_ema(df_15m["close"], 50)
    ema_200 = calcular_ema(df_15m["close"], 200)

    st.session_state.ultimo_preco = preco
    st.session_state.rsi_15m = rsi_15m
    st.session_state.rsi_4h = rsi_4h
    st.session_state.rsi_1w = rsi_1w
    st.session_state.ema_20 = ema_20
    st.session_state.ema_50 = ema_50
    st.session_state.ema_200 = ema_200
    st.session_state.erro_tela = ""

    horario_curto = datetime.now().strftime("%d/%m %H:%M")
    preco_txt = "-" if preco is None else f"{preco:.6f}"
    rsi15_txt = "-" if rsi_15m is None else f"RSI {rsi_15m:.2f}"
    rsi4h_txt = "-" if rsi_4h is None else f"RSI {rsi_4h:.2f}"
    rsi1w_txt = "-" if rsi_1w is None else f"RSI {rsi_1w:.2f}"

    registrar_linha("logs_datahora", horario_curto)
    registrar_linha("logs_preco", preco_txt)
    registrar_linha("rsi_logs_15m", rsi15_txt)
    registrar_linha("rsi_logs_4h", rsi4h_txt)
    registrar_linha("rsi_logs_1w", rsi1w_txt)

    registrar_log_simples(token, preco)


def montar_lista(lista: list[str]) -> str:
    if not lista:
        return "Sem dados ainda."
    return "\n".join(lista[:12])


def fmt_num(valor: float | None, casas: int = 2) -> str:
    if valor is None:
        return "-"
    return f"{valor:.{casas}f}"


# =========================================
# TOPO
# =========================================
st.markdown('<div class="top-card">', unsafe_allow_html=True)
st.markdown('<div class="top-title">🤖 LuxAlgoClone Monitor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="top-subtitle">Somente exibição visual: gráfico, RSI, EMAs e log simples.</div>',
    unsafe_allow_html=True,
)

col_token_1, col_token_2, col_token_3, col_token_4 = st.columns([4, 1, 1, 1])

with col_token_1:
    token_digitado = st.text_input(
        "Digite o token base. O sistema sempre usará /USDT",
        key="token_input_widget",
        placeholder="Ex: AVAX, BTC, ETH, SOL, PEPE",
    ).strip().upper()

with col_token_2:
    confirmar = st.button("✅ Confirmar", use_container_width=True)

with col_token_3:
    parar = st.button("⛔ Parar monitor", use_container_width=True)

with col_token_4:
    atualizar = st.button("🔄 Atualizar", use_container_width=True)

if confirmar:
    if not token_digitado:
        st.session_state.erro_tela = "Digite um token antes de confirmar."
    else:
        if token_digitado != st.session_state.token_confirmado:
            limpar_dados_visuais()
        st.session_state.token_confirmado = token_digitado
        st.session_state.monitor_ativo = True
        try:
            atualizar_tela(token_digitado)
        except Exception as e:
            st.session_state.erro_tela = str(e)
        st.rerun()

if parar:
    st.session_state.monitor_ativo = False
    st.rerun()

if atualizar:
    try:
        atualizar_tela(st.session_state.token_confirmado)
    except Exception as e:
        st.session_state.erro_tela = str(e)
    st.rerun()

if st.session_state.monitor_ativo and contador_refresh > 0:
    try:
        atualizar_tela(st.session_state.token_confirmado)
    except Exception as e:
        st.session_state.erro_tela = str(e)

ativo_atual = f"{st.session_state.token_confirmado}/USDT"

m1, m2, m3, m4, m5 = st.columns(5)

with m1:
    st.markdown('<div class="metric-label">Ativo</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{ativo_atual}</div>', unsafe_allow_html=True)

with m2:
    ultimo_preco_txt = "-"
    if st.session_state.ultimo_preco is not None:
        ultimo_preco_txt = f"${st.session_state.ultimo_preco:,.6f}"
    st.markdown('<div class="metric-label">Último valor</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{ultimo_preco_txt}</div>', unsafe_allow_html=True)

with m3:
    st.markdown('<div class="metric-label">EMA 20</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{fmt_num(st.session_state.ema_20, 6)}</div>', unsafe_allow_html=True)

with m4:
    st.markdown('<div class="metric-label">EMA 50</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{fmt_num(st.session_state.ema_50, 6)}</div>', unsafe_allow_html=True)

with m5:
    st.markdown('<div class="metric-label">EMA 200</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{fmt_num(st.session_state.ema_200, 6)}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# =========================================
# ERRO
# =========================================
if st.session_state.erro_tela:
    st.error(st.session_state.erro_tela)


# =========================================
# TABELAS VISUAIS
# =========================================
c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown('<div class="plain-title">hora</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="data-box">
            <div class="data-list">{montar_lista(st.session_state.logs_datahora)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown('<div class="plain-title">valor</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="data-box">
            <div class="data-list">{montar_lista(st.session_state.logs_preco)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown('<div class="col-title">RSI 15 minutos</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="data-box">
            <div class="data-list">{montar_lista(st.session_state.rsi_logs_15m)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown('<div class="col-title">RSI 4 horas</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="data-box">
            <div class="data-list">{montar_lista(st.session_state.rsi_logs_4h)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c5:
    st.markdown('<div class="col-title">RSI Semanal</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="data-box">
            <div class="data-list">{montar_lista(st.session_state.rsi_logs_1w)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================
# GRÁFICO
# =========================================
st.subheader("📊 Gráfico TradingView")

if st.session_state.token_confirmado:
    tradingview_symbol = f"BINANCE:{st.session_state.token_confirmado}USDT"

    tradingview_widget = f"""
    <div class="tradingview-widget-container">
      <div id="tradingview_chart"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": 620,
        "symbol": "{tradingview_symbol}",
        "interval": "15",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "pt",
        "toolbar_bg": "#0e1117",
        "enable_publishing": false,
        "hide_side_toolbar": false,
        "allow_symbol_change": false,
        "container_id": "tradingview_chart"
      }});
      </script>
    </div>
    """

    st.components.v1.html(tradingview_widget, height=670)
else:
    st.info("O gráfico aparecerá depois da atualização.")


# =========================================
# LOG SIMPLES
# =========================================
st.subheader("🧾 Logs do Bot")

if st.session_state.logs_bot:
    df_logs = pd.DataFrame(st.session_state.logs_bot)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
else:
    st.info("Ainda não há logs.")
