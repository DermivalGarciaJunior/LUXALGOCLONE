import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="LuxAlgoClone", layout="wide", page_icon="📈")

# =========================================
# CONFIG
# =========================================
REFRESH_MINUTOS = 3
REFRESH_MS = REFRESH_MINUTOS * 60 * 1000

# =========================================
# AUTO REFRESH
# =========================================
st_autorefresh(interval=REFRESH_MS, key="refresh")

# =========================================
# INPUT DO USUÁRIO
# =========================================
st.title("🤖 LuxAlgoClone Monitor")

token_input = st.text_input("Digite o token (ex: BTC, ETH, AVAX)", value="AVAX")
token = token_input.strip().upper()

ativo = f"{token}/USDT"
symbol_tradingview = f"BINANCE:{token}USDT"

# =========================================
# ESTADO
# =========================================
if "historico" not in st.session_state:
    st.session_state.historico = []

if "logs" not in st.session_state:
    st.session_state.logs = []

if "posicao" not in st.session_state:
    st.session_state.posicao = "SEM POSIÇÃO"

# =========================================
# FUNÇÕES
# =========================================
def registrar_log(acao, preco, detalhe):
    agora = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.insert(0, {
        "Hora": agora,
        "Token": token,
        "Preço": round(preco, 6),
        "Ação": acao,
        "Detalhe": detalhe
    })

def buscar_preco():
    # usamos Binance pública via API simples
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={token}USDT"
    r = requests.get(url, timeout=10)
    data = r.json()

    if "price" not in data:
        raise Exception("Token não encontrado")

    return float(data["price"])

# =========================================
# MONITORAMENTO
# =========================================
try:
    preco = buscar_preco()
    st.session_state.historico.append(preco)
    st.session_state.historico = st.session_state.historico[-20:]

    registrar_log("CHECK", preco, "Monitorando mercado")

except Exception as e:
    st.error(f"Erro: {e}")
    st.stop()

# =========================================
# SINAL SIMPLES (média)
# =========================================
if len(st.session_state.historico) > 5:
    media_curta = sum(st.session_state.historico[-3:]) / 3
    media_longa = sum(st.session_state.historico[-6:]) / 6

    if media_curta > media_longa:
        sinal = "LONG 🟢"
    elif media_curta < media_longa:
        sinal = "SHORT 🔴"
    else:
        sinal = "AGUARDANDO ⚪"
else:
    sinal = "AGUARDANDO ⚪"

# =========================================
# DECISÃO
# =========================================
if st.session_state.posicao == "SEM POSIÇÃO":
    if "LONG" in sinal:
        st.session_state.posicao = "LONG"
        registrar_log("ENTRADA", preco, "Entrou em LONG")

    elif "SHORT" in sinal:
        st.session_state.posicao = "SHORT"
        registrar_log("ENTRADA", preco, "Entrou em SHORT")

elif st.session_state.posicao == "LONG":
    if "SHORT" in sinal:
        registrar_log("SAÍDA", preco, "Saiu do LONG")
        st.session_state.posicao = "SHORT"
        registrar_log("ENTRADA", preco, "Entrou em SHORT")

elif st.session_state.posicao == "SHORT":
    if "LONG" in sinal:
        registrar_log("SAÍDA", preco, "Saiu do SHORT")
        st.session_state.posicao = "LONG"
        registrar_log("ENTRADA", preco, "Entrou em LONG")

# =========================================
# STATUS
# =========================================
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Ativo", ativo)

with col2:
    st.metric("Preço", f"${preco:.4f}")

with col3:
    st.metric("Sinal", sinal)

st.info(f"Posição atual: {st.session_state.posicao}")

# =========================================
# TRADINGVIEW
# =========================================
st.write("📊 Gráfico")

tv = f"""
<div class="tradingview-widget-container">
  <div id="tv_chart"></div>
  <script src="https://s3.tradingview.com/tv.js"></script>
  <script>
  new TradingView.widget({{
    "width": "100%",
    "height": 600,
    "symbol": "{symbol_tradingview}",
    "interval": "15",
    "theme": "dark",
    "style": "1",
    "locale": "pt",
    "container_id": "tv_chart"
  }});
  </script>
</div>
"""

st.components.v1.html(tv, height=650)

# =========================================
# LOGS
# =========================================
st.write("📜 Logs")

if st.session_state.logs:
    df = pd.DataFrame(st.session_state.logs)
    st.dataframe(df, use_container_width=True)
else:
    st.write("Sem logs ainda")

# =========================================
# FINAL
# =========================================
st.success("Rodando automaticamente a cada 3 minutos")
