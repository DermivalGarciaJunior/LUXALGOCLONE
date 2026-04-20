import streamlit as st
import time

st.set_page_config(page_title="LuxAlgoClone", layout="wide")

# =========================
# DEBUG INICIAL
# =========================
st.write("🚀 INICIANDO APLICAÇÃO...")
time.sleep(1)

st.write("⚙️ Carregando bibliotecas...")
time.sleep(1)

# =========================
# TESTE DE IMPORTS
# =========================
try:
    import ccxt
    st.write("✅ CCXT carregado")
except Exception as e:
    st.error(f"❌ Erro ao carregar CCXT: {e}")
    st.stop()

try:
    import pandas as pd
    st.write("✅ Pandas carregado")
except Exception as e:
    st.error(f"❌ Erro ao carregar Pandas: {e}")
    st.stop()

# =========================
# TESTE BINANCE
# =========================
st.write("🌐 Conectando na Binance...")
time.sleep(1)

try:
    exchange = ccxt.binance({
        "enableRateLimit": True,
        "timeout": 10000,
    })
    st.write("✅ Conexão criada")
except Exception as e:
    st.error(f"❌ Erro ao criar conexão: {e}")
    st.stop()

# =========================
# TESTE FETCH
# =========================
st.write("📡 Buscando dados...")
time.sleep(1)

try:
    candles = exchange.fetch_ohlcv("AVAX/USDT", timeframe="15m", limit=10)
    st.write("✅ Dados recebidos da Binance")
except Exception as e:
    st.error(f"❌ Erro ao buscar dados: {e}")
    st.stop()

# =========================
# TESTE DATAFRAME
# =========================
st.write("📊 Convertendo dados...")
time.sleep(1)

try:
    df = pd.DataFrame(candles)
    st.write("✅ DataFrame criado")
except Exception as e:
    st.error(f"❌ Erro no DataFrame: {e}")
    st.stop()

# =========================
# FINAL
# =========================
st.success("🎯 APP FUNCIONANDO ATÉ AQUI")
st.write(df)
