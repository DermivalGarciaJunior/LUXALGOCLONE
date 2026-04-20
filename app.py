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


inicializar_estado()

# =========================================
# AUTO-REFRESH
# Só atualiza automaticamente se o monitor estiver ativo
# =========================================
if st.session_state.monitor_ativo:
    contador_refresh = st_autorefresh(interval=REFRESH_MS, key="monitor_refresh")
else:
    contador_refresh = 0

# =========================================
# FUNÇÕES
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


def buscar_preco_okx(token: str) -> float:
    """
    Busca o último preço em USDT na OKX.
    Exemplo de símbolo: AVAX-USDT
    """
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


def processar_monitoramento() -> None:
    token = st.session_state.token_confirmado

    if not token:
        return

    try:
        preco = buscar_preco_okx(token)
        adicionar_historico(preco)

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


# =========================================
# CABEÇALHO
# =========================================
st.title("🤖 LuxAlgoClone Monitor")
st.caption("Escolha o token e confirme. O monitoramento só começa depois da confirmação.")

# =========================================
# ESCOLHA DO TOKEN
# =========================================
col_token_1, col_token_2, col_token_3 = st.columns([3, 1, 1])

with col_token_1:
    token_digitado = st.text_input(
        "Digite o token base. O sistema sempre usará /USDT",
        key="token_input_widget",
        placeholder="Ex: AVAX, BTC, ETH, SOL, PEPE",
    ).strip().upper()

with col_token_2:
    confirmar = st.button("✅ Confirmar token", use_container_width=True)

with col_token_3:
    parar = st.button("⛔ Parar monitor", use_container_width=True)

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

token_confirmado = st.session_state.token_confirmado
ativo_atual = f"{token_confirmado}/USDT" if token_confirmado else "-"

# =========================================
# BOTÃO MANUAL
# =========================================
col_botao_1, col_botao_2 = st.columns([1, 4])

with col_botao_1:
    atualizar_agora = st.button("🔄 Atualizar agora", use_container_width=True)

with col_botao_2:
    st.caption("Use este botão para forçar uma nova leitura sem esperar os 3 minutos.")

if atualizar_agora and st.session_state.monitor_ativo and token_confirmado:
    processar_monitoramento()
    st.rerun()

# =========================================
# EXECUÇÃO AUTOMÁTICA
# =========================================
if st.session_state.monitor_ativo and token_confirmado and contador_refresh > 0:
    processar_monitoramento()

# =========================================
# STATUS SUPERIOR
# =========================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Ativo", ativo_atual)

with c2:
    preco_fmt = "-"
    if st.session_state.ultimo_preco is not None:
        preco_fmt = f"${st.session_state.ultimo_preco:,.6f}"
    st.metric("Último valor", preco_fmt)

with c3:
    st.metric("Sinal atual", st.session_state.ultimo_sinal)

with c4:
    status_bot = "ATIVO" if st.session_state.monitor_ativo else "PARADO"
    st.metric("Status do bot", status_bot)

# =========================================
# STATUS DO MONITOR
# =========================================
st.subheader("📋 Status do Monitor")

if not token_confirmado:
    st.warning("Digite o token e clique em 'Confirmar token' para iniciar o monitoramento.")
else:
    st.info(f"Token escolhido: {token_confirmado}/USDT")

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

if token_confirmado:
    tradingview_symbol = f"BINANCE:{token_confirmado}USDT"

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
