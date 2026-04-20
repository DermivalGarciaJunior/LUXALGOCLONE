import streamlit as st

st.set_page_config(page_title="LuxAlgoClone", layout="wide")

# =========================
# INÍCIO
# =========================
st.write("🚀 INICIANDO APLICAÇÃO...")
st.write("📊 Carregando gráfico TradingView...")

# =========================
# WIDGET TRADINGVIEW
# =========================
tradingview_widget = """
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div id="tradingview_chart"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({
    "width": "100%",
    "height": 600,
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
<!-- TradingView Widget END -->
"""

st.components.v1.html(tradingview_widget, height=650)

# =========================
# FINAL
# =========================
st.success("🎯 TradingView carregado com sucesso!")
st.write("Agora seu app funciona sem depender de Binance ou API.")
