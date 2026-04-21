import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LuxAlgoClone", layout="wide", page_icon="📈")


# =========================================
# CONFIGURAÇÕES
# =========================================
REFRESH_MINUTOS = 3
REFRESH_MS = REFRESH_MINUTOS * 60 * 1000
MAX_HISTORICO = 50
MAX_LOGS = 300
MAX_RSI_LOGS = 50


# =========================================
# ESTILO
# =========================================
st.markdown(
    """
    <style>
    .top-card {
        background: #07111f;
        border-radius: 10px;
        padding: 18px 18px 8px 18px;
        margin-bottom: 18px;
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
    .rsi-box {
        background: #f3f3f3;
        color: #111;
        border-radius: 4px;
        padding: 14px 16px;
        min-height: 320px;
    }
    .rsi-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .rsi-current {
        font-size: 1.05rem;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .rsi-list {
        font-size: 0.95rem;
        line-height: 1.45;
        white-space: pre-wrap;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================
# ESTADO INICIAL
# =========================================
def inicializar_estado() -> None:
    if "token_confirmado" not in st.session_state:
        st.session_state.token_confirmado = ""

    if "monitor_ativo" not in st.session_state:
        st.session_state.monitor_ativo = False

    if "historico" not in st.session_state:
        st.session_state.historico = []

    if "logs" not in st.session_state:
        st.session_state.logs = []

    if "posicao" not in st.session_state:
        st.session_state.posicao = "SEM POSIÇÃO"

    if "ultimo_preco" not in st.session_state:
        st.session_state.ultimo_preco = None

    if "ultimo_update" not in st.session_state:
        st.session_state.ultimo_update = "-"

    if "ultimo_sinal" not in st.session_state:
        st.session_state.ultimo_sinal = "AGUARDANDO"

    if "ultima_acao" not in st.session_state:
        st.session_state.ultima_acao = "Nenhuma"

    if "erro_monitoramento" not in st.session_state:
        st.session_state.erro_monitoramento = ""

    if "token_input_widget" not in st.session_state:
        st.session_state.token_input_widget = "AVAX"

    if "rsi_logs_15m" not in st.session_state:
        st.session_state.rsi_logs_15m = []

    if "rsi_logs_4h" not in st.session_state:
        st.session_state.rsi_logs_4h = []

    if "rsi_logs_1w" not in st.session_state:
        st.session_state.rsi_logs_1w = []

    if "rsi_atual_15m" not in st.session_state:
        st.session_state.rsi_atual_15m = None

    if "rsi_atual_4h" not in st.session_state:
        st.session_state.rsi_atual_4h = None

    if "rsi_atual_1w" not in st.session_state:
        st.session_state.rsi_atual_1w = None


inicializar_estado()


# =========================================
# AUTO-REFRESH
# =========================================
if st.session_state.monitor_ativo:
    contador_refresh = st_autorefresh(interval=REFRESH_MS, key="monitor_refresh")
else:
    contador_refresh = 0


# =========================================
# FUNÇÕES AUXILIARES
# =========================================
def limpar_monitoramento() -> None:
    st.session_state.historico = []
    st.session_state.logs = []
    st.session_state.posicao = "SEM POSIÇÃO"
    st.session_state.ultimo_preco = None
    st.session_state.ultimo_update = "-"
    st.session_state.ultimo_sinal = "AGUARDANDO"
    st.session_state.ultima_acao = "Nenhuma"
    st.session_state.erro_monitoramento = ""
    st.session_state.rsi_logs_15m = []
    st.session_state.rsi_logs_4h = []
    st.session_state.rsi_logs_1w = []
    st.session_state.rsi_atual_15m = None
    st.session_state.rsi_atual_4h = None
    st.session_state.rsi_atual_1w = None


def registrar_log(acao: str, preco: float, detalhe: str) -> None:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    token = st.session_state.token_confirmado or "-"
    novo = {
        "Horário": agora,
        "Token": token,
        "Preço": round(preco, 6),
        "Ação": acao,
        "Detalhe": detalhe,
    }
    st.session_state.logs.insert(0, novo)
    st.session_state.logs = st.session_state.logs[:MAX_LOGS]


def registrar_rsi_log(janela: str, valor: float | None) -> None:
    agora = datetime.now().strftime("%d/%m %H:%M")
    texto_valor = "-" if valor is None else f"{valor:.2f}"

    linha = {
        "horario": agora,
        "valor": texto_valor,
    }

    if janela == "15m":
        st.session_state.rsi_logs_15m.insert(0, linha)
        st.session_state.rsi_logs_15m = st.session_state.rsi_logs_15m[:MAX_RSI_LOGS]
    elif janela == "4h":
        st.session_state.rsi_logs_4h.insert(0, linha)
        st.session_state.rsi_logs_4h = st.session_state.rsi_logs_4h[:MAX_RSI_LOGS]
    elif janela == "1w":
        st.session_state.rsi_logs_1w.insert(0, linha)
        st.session_state.rsi_logs_1w = st.session_state.rsi_logs_1w[:MAX_RSI_LOGS]


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


def buscar_candles_okx(token: str, bar: str, limit: int = 100) -> pd.DataFrame:
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


def adicionar_historico(preco: float) -> None:
    st.session_state.historico.append({
        "timestamp": datetime.now(),
        "preco": preco,
    })
    st.session_state.historico = st.session_state.historico[-MAX_HISTORICO:]


def calcular_sinal() -> tuple[str, float | None, float | None]:
    if len(st.session_state.historico) < 8:
        return "AGUARDANDO", None, None

    df_hist = pd.DataFrame(st.session_state.historico)

    media_curta = df_hist["preco"].tail(3).mean()
    media_longa = df_hist["preco"].tail(8).mean()

    if media_curta > media_longa * 1.001:
        return "LONG OK", media_curta, media_longa

    if media_curta < media_longa * 0.999:
        return "SHORT OK", media_curta, media_longa

    return "AGUARDANDO", media_curta, media_longa


def atualizar_rsis(token: str) -> None:
    df_15m = buscar_candles_okx(token, "15m", 100)
    df_4h = buscar_candles_okx(token, "4H", 100)
    df_1w = buscar_candles_okx(token, "1W", 100)

    rsi_15m = calcular_rsi(df_15m["close"], 14)
    rsi_4h = calcular_rsi(df_4h["close"], 14)
    rsi_1w = calcular_rsi(df_1w["close"], 14)

    st.session_state.rsi_atual_15m = rsi_15m
    st.session_state.rsi_atual_4h = rsi_4h
    st.session_state.rsi_atual_1w = rsi_1w

    registrar_rsi_log("15m", rsi_15m)
    registrar_rsi_log("4h", rsi_4h)
    registrar_rsi_log("1w", rsi_1w)


def processar_monitoramento() -> None:
    token = st.session_state.token_confirmado

    if not token:
        return

    try:
        preco = buscar_preco_okx(token)
        adicionar_historico(preco)
        atualizar_rsis(token)

        st.session_state.ultimo_preco = preco
        st.session_state.ultimo_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.session_state.erro_monitoramento = ""

        sinal, media_curta, media_longa = calcular_sinal()
        st.session_state.ultimo_sinal = sinal

        detalhe_check = "Verificação periódica"
        if media_curta is not None and media_longa is not None:
            detalhe_check += f" | MM curta: {media_curta:.6f} | MM longa: {media_longa:.6f}"

        registrar_log("CHECK", preco, f"{sinal} | {detalhe_check}")

        posicao = st.session_state.posicao

        if posicao == "SEM POSIÇÃO":
            if sinal == "LONG OK":
                st.session_state.posicao = "LONG"
                st.session_state.ultima_acao = "ENTRADA LONG"
                registrar_log("ENTRADA", preco, "Entrou em LONG")
            elif sinal == "SHORT OK":
                st.session_state.posicao = "SHORT"
                st.session_state.ultima_acao = "ENTRADA SHORT"
                registrar_log("ENTRADA", preco, "Entrou em SHORT")
            else:
                st.session_state.ultima_acao = "Aguardando sinal"

        elif posicao == "LONG":
            if sinal == "SHORT OK":
                registrar_log("SAÍDA", preco, "Saiu do LONG por reversão")
                st.session_state.posicao = "SHORT"
                st.session_state.ultima_acao = "REVERSÃO LONG -> SHORT"
                registrar_log("ENTRADA", preco, "Entrou em SHORT por reversão")
            else:
                st.session_state.ultima_acao = "LONG mantido"

        elif posicao == "SHORT":
            if sinal == "LONG OK":
                registrar_log("SAÍDA", preco, "Saiu do SHORT por reversão")
                st.session_state.posicao = "LONG"
                st.session_state.ultima_acao = "REVERSÃO SHORT -> LONG"
                registrar_log("ENTRADA", preco, "Entrou em LONG por reversão")
            else:
                st.session_state.ultima_acao = "SHORT mantido"

    except Exception as e:
        st.session_state.erro_monitoramento = str(e)
        preco_log = st.session_state.ultimo_preco if st.session_state.ultimo_preco is not None else 0.0
        registrar_log("ERRO", preco_log, f"Falha no monitoramento: {e}")


def formatar_lista_rsi(lista: list[dict]) -> str:
    if not lista:
        return "Sem leituras ainda."

    linhas = [f"{item['horario']}  |  RSI {item['valor']}" for item in lista[:12]]
    return "\n".join(linhas)


# =========================================
# CABEÇALHO / INÍCIO NO NOVO LAYOUT
# =========================================
st.markdown('<div class="top-card">', unsafe_allow_html=True)
st.markdown('<div class="top-title">🤖 LuxAlgoClone Monitor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="top-subtitle">Escolha o token e confirme. O monitoramento só começa depois da confirmação.</div>',
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
    atualizar_agora = st.button("🔄 Atualizar", use_container_width=True)

if confirmar:
    if not token_digitado:
        st.error("Digite um token antes de confirmar.")
    else:
        if token_digitado != st.session_state.token_confirmado:
            limpar_monitoramento()

        st.session_state.token_confirmado = token_digitado
        st.session_state.monitor_ativo = True
        st.session_state.ultima_acao = f"Token confirmado: {token_digitado}/USDT"
        processar_monitoramento()
        st.rerun()

if parar:
    st.session_state.monitor_ativo = False
    st.session_state.ultima_acao = "Monitoramento pausado"
    st.rerun()

if atualizar_agora and st.session_state.monitor_ativo and st.session_state.token_confirmado:
    processar_monitoramento()
    st.rerun()

if st.session_state.monitor_ativo and st.session_state.token_confirmado and contador_refresh > 0:
    processar_monitoramento()

ativo_atual = f"{st.session_state.token_confirmado}/USDT" if st.session_state.token_confirmado else "-"

m1, m2, m3, m4 = st.columns(4)

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
    st.markdown('<div class="metric-label">Sinal atual</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{st.session_state.ultimo_sinal}</div>', unsafe_allow_html=True)

with m4:
    status_bot = "ATIVO" if st.session_state.monitor_ativo else "PARADO"
    st.markdown('<div class="metric-label">Status do bot</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-value">{status_bot}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# =========================================
# JANELAS DE RSI
# =========================================
r1, r2, r3 = st.columns(3)

with r1:
    st.markdown('<div class="rsi-box">', unsafe_allow_html=True)
    st.markdown('<div class="rsi-title">Janela 01</div>', unsafe_allow_html=True)
    valor_15 = "-" if st.session_state.rsi_atual_15m is None else f"{st.session_state.rsi_atual_15m:.2f}"
    st.markdown(f'<div class="rsi-current">RSI 15 minutos: {valor_15}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="rsi-list">{formatar_lista_rsi(st.session_state.rsi_logs_15m)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with r2:
    st.markdown('<div class="rsi-box">', unsafe_allow_html=True)
    st.markdown('<div class="rsi-title">Janela 02</div>', unsafe_allow_html=True)
    valor_4h = "-" if st.session_state.rsi_atual_4h is None else f"{st.session_state.rsi_atual_4h:.2f}"
    st.markdown(f'<div class="rsi-current">RSI 4 horas: {valor_4h}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="rsi-list">{formatar_lista_rsi(st.session_state.rsi_logs_4h)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

with r3:
    st.markdown('<div class="rsi-box">', unsafe_allow_html=True)
    st.markdown('<div class="rsi-title">Janela 03</div>', unsafe_allow_html=True)
    valor_1w = "-" if st.session_state.rsi_atual_1w is None else f"{st.session_state.rsi_atual_1w:.2f}"
    st.markdown(f'<div class="rsi-current">RSI 1 semana: {valor_1w}</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="rsi-list">{formatar_lista_rsi(st.session_state.rsi_logs_1w)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# =========================================
# STATUS DO MONITOR
# =========================================
st.subheader("📋 Status do Monitor")

if not st.session_state.token_confirmado:
    st.warning("Digite o token e clique em 'Confirmar' para iniciar o monitoramento.")
else:
    st.info(f"Token escolhido: {st.session_state.token_confirmado}/USDT")

if st.session_state.erro_monitoramento:
    st.error(f"Erro no monitoramento: {st.session_state.erro_monitoramento}")
else:
    st.info(f"⏰ Última verificação: {st.session_state.ultimo_update}")

if st.session_state.ultimo_sinal == "LONG OK":
    st.success("🟢 Sinal LONG OK")
elif st.session_state.ultimo_sinal == "SHORT OK":
    st.error("🔴 Sinal SHORT OK")
else:
    st.warning("🟡 Aguardando sinal")

st.info(f"📌 Última ação: {st.session_state.ultima_acao}")
st.info(f"📍 Posição atual: {st.session_state.posicao}")

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
    st.info("O gráfico aparecerá depois que você confirmar o token.")

# =========================================
# LOGS
# =========================================
st.subheader("🧾 Logs do Bot")

if st.session_state.logs:
    df_logs = pd.DataFrame(st.session_state.logs)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
else:
    st.info("Ainda não há logs.")

# =========================================
# RODAPÉ
# =========================================
if st.session_state.monitor_ativo:
    st.success(f"🎯 Monitoramento ativo a cada {REFRESH_MINUTOS} minutos")
else:
    st.warning("⏸️ Monitoramento parado")
