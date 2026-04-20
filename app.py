import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LuxAlgoClone", layout="wide", page_icon="📈")


# =========================================
# CONFIGURAÇÕES
# =========================================
ATIVO = "AVAX/USD"
REFRESH_MINUTOS = 3
REFRESH_MS = REFRESH_MINUTOS * 60 * 1000
MAX_HISTORICO_PRECO = 50
MAX_LOGS = 200


# =========================================
# AUTO-REFRESH
# =========================================
contador_execucoes = st_autorefresh(
    interval=REFRESH_MS,
    key="monitor_refresh",
)


# =========================================
# ESTADO INICIAL
# =========================================
def inicializar_estado() -> None:
    if "historico_precos" not in st.session_state:
        st.session_state.historico_precos = []

    if "logs_operacoes" not in st.session_state:
        st.session_state.logs_operacoes = []

    if "ultima_acao" not in st.session_state:
        st.session_state.ultima_acao = "Nenhuma"

    if "status_sinal" not in st.session_state:
        st.session_state.status_sinal = "AGUARDANDO"

    if "posicao_atual" not in st.session_state:
        st.session_state.posicao_atual = "SEM POSIÇÃO"

    if "ultimo_preco" not in st.session_state:
        st.session_state.ultimo_preco = None

    if "ultimo_update" not in st.session_state:
        st.session_state.ultimo_update = None

    if "erro_monitoramento" not in st.session_state:
        st.session_state.erro_monitoramento = ""


inicializar_estado()


# =========================================
# FUNÇÕES
# =========================================
def registrar_log(acao: str, preco: float, detalhe: str) -> None:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    novo = {
        "Horário": agora,
        "Preço": round(preco, 4),
        "Ação": acao,
        "Detalhe": detalhe,
    }
    st.session_state.logs_operacoes.insert(0, novo)
    st.session_state.logs_operacoes = st.session_state.logs_operacoes[:MAX_LOGS]


def buscar_preco_avax_usd() -> float:
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "avalanche-2",
        "vs_currencies": "usd",
    }
    resposta = requests.get(url, params=params, timeout=20)
    resposta.raise_for_status()

    dados = resposta.json()
    preco = dados["avalanche-2"]["usd"]
    return float(preco)


def adicionar_preco_historico(preco: float) -> None:
    agora = datetime.now()
    st.session_state.historico_precos.append({
        "timestamp": agora,
        "preco": preco,
    })
    st.session_state.historico_precos = st.session_state.historico_precos[-MAX_HISTORICO_PRECO:]


def calcular_sinal():
    historico = st.session_state.historico_precos

    if len(historico) < 8:
        return "AGUARDANDO", None, None

    df_hist = pd.DataFrame(historico)
    media_curta = df_hist["preco"].tail(3).mean()
    media_longa = df_hist["preco"].tail(8).mean()

    if media_curta > media_longa * 1.001:
        return "LONG OK", media_curta, media_longa

    if media_curta < media_longa * 0.999:
        return "SHORT OK", media_curta, media_longa

    return "AGUARDANDO", media_curta, media_longa


def processar_monitoramento() -> None:
    try:
        preco = buscar_preco_avax_usd()
        adicionar_preco_historico(preco)

        st.session_state.ultimo_preco = preco
        st.session_state.ultimo_update = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.session_state.erro_monitoramento = ""

        status, media_curta, media_longa = calcular_sinal()
        st.session_state.status_sinal = status

        detalhe_monitor = "Monitoramento periódico"

        if media_curta is not None and media_longa is not None:
            detalhe_monitor += f" | MM curta: {media_curta:.4f} | MM longa: {media_longa:.4f}"

        registrar_log("VERIFICAÇÃO", preco, f"{status} | {detalhe_monitor}")

        posicao = st.session_state.posicao_atual

        if posicao == "SEM POSIÇÃO":
            if status == "LONG OK":
                st.session_state.posicao_atual = "LONG"
                st.session_state.ultima_acao = "ENTRADA LONG"
                registrar_log("ENTRADA", preco, "Sinal LONG confirmado")
            elif status == "SHORT OK":
                st.session_state.posicao_atual = "SHORT"
                st.session_state.ultima_acao = "ENTRADA SHORT"
                registrar_log("ENTRADA", preco, "Sinal SHORT confirmado")
            else:
                st.session_state.ultima_acao = "Aguardando sinal"

        elif posicao == "LONG":
            if status == "SHORT OK":
                registrar_log("SAÍDA", preco, "Fechando LONG por reversão")
                st.session_state.posicao_atual = "SHORT"
                st.session_state.ultima_acao = "REVERSÃO LONG -> SHORT"
                registrar_log("ENTRADA", preco, "Nova ENTRADA SHORT por reversão")
            else:
                st.session_state.ultima_acao = "LONG mantido"

        elif posicao == "SHORT":
            if status == "LONG OK":
                registrar_log("SAÍDA", preco, "Fechando SHORT por reversão")
                st.session_state.posicao_atual = "LONG"
                st.session_state.ultima_acao = "REVERSÃO SHORT -> LONG"
                registrar_log("ENTRADA", preco, "Nova ENTRADA LONG por reversão")
            else:
                st.session_state.ultima_acao = "SHORT mantido"

    except Exception as e:
        st.session_state.erro_monitoramento = str(e)
        registrar_log("ERRO", st.session_state.ultimo_preco or 0.0, f"Falha no monitoramento: {e}")


# =========================================
# EXECUÇÃO DO MONITORAMENTO
# =========================================
if contador_execucoes == 0 and not st.session_state.historico_precos:
    processar_monitoramento()
elif contador_execucoes > 0:
    processar_monitoramento()


# =========================================
# CABEÇALHO
# =========================================
st.title("🤖 LuxAlgoClone Monitor")
st.caption(f"Atualização automática a cada {REFRESH_MINUTOS} minutos enquanto a página estiver aberta.")

if st.button("🔄 Atualizar agora"):
    processar_monitoramento()
    st.rerun()


# =========================================
# STATUS SUPERIOR
# =========================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Ativo", ATIVO)

with c2:
    ultimo_preco_fmt = f"${st.session_state.ultimo_preco:,.4f}" if st.session_state.ultimo_preco is not None else "-"
    st.metric("Último valor", ultimo_preco_fmt)

with c3:
    st.metric("Sinal atual", st.session_state.status_sinal)

with c4:
    st.metric("Posição atual", st.session_state.posicao_atual)


# =========================================
# MENSAGENS DE MONITORAMENTO
# =========================================
st.subheader("📋 Status do Monitor")

if st.session_state.erro_monitoramento:
    st.error(f"Erro no monitoramento: {st.session_state.erro_monitoramento}")
else:
    st.info(f"⏰ Última verificação: {st.session_state.ultimo_update or '-'}")

if st.session_state.status_sinal == "LONG OK":
    st.success("🟢 Sinal LONG OK")
elif st.session_state.status_sinal == "SHORT OK":
    st.error("🔴 Sinal SHORT OK")
else:
    st.warning("🟡 Aguardando sinal")

st.info(f"📌 Última ação: {st.session_state.ultima_acao}")
st.info(f"🤖 Situação do bot: {st.session_state.posicao_atual}")


# =========================================
# GRÁFICO TRADINGVIEW
# =========================================
st.subheader("📊 Gráfico TradingView")

tradingview_widget = """
<div class="tradingview-widget-container">
  <div id="tradingview_chart"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "width": "100%",
    "height": 620,
    "symbol": "BINANCE:AVAXUSDT",
    "interval": "15",
    "timezone": "Etc/UTC",
    "theme": "dark",
    "style": "1",
    "locale": "pt",
    "toolbar_bg": "#0e1117",
    "enable_publishing": false,
    "hide_side_toolbar": false,
    "allow_symbol_change": true,
    "container_id": "tradingview_chart"
  });
  </script>
</div>
"""

st.components.v1.html(tradingview_widget, height=670)


# =========================================
# LOGS NA TELA
# =========================================
st.subheader("🧾 Logs do Bot")

if st.session_state.logs_operacoes:
    df_logs = pd.DataFrame(st.session_state.logs_operacoes)
    st.dataframe(df_logs, use_container_width=True, hide_index=True)
else:
    st.info("Ainda não há logs.")


# =========================================
# RODAPÉ
# =========================================
st.success("🎯 Monitoramento ativo")
st.caption("Este app monitora enquanto a página estiver aberta. Para rodar 24h em segundo plano, será preciso usar um servidor/VPS.")
