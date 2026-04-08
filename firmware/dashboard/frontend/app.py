import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ASCM Smart Dashboard", layout="wide", page_icon="🌤️")

# --- SIDEBAR: CONFIGURAÇÕES SMART ---
st.sidebar.title("⚙️ Configurações Smart")
city = st.sidebar.text_input("Localização (Cidade)", "Sao Paulo")
eff_limit = st.sidebar.slider("Limiar de Sujeira (%)", 5, 30, 10)
temp_limit = st.sidebar.slider("Delta de Temperatura (°C)", 2, 10, 5)
auto_on = st.sidebar.toggle("Automação Ativa", True)

if st.sidebar.button("Salvar Configurações"):
    new_cfg = {
        "city": city,
        "efficiency_threshold": float(eff_limit),
        "temp_delta_limit": float(temp_limit),
        "automation_enabled": auto_on
    }
    requests.post("http://localhost:8000/config/update", json=new_cfg)
    st.sidebar.success("Configurações aplicadas!")

# --- CABEÇALHO COM CLIMA EXTERNO ---
st.title("🌤️ ASCM Smart Monitoring")

# Mock de dados de clima para o frontend
weather_info = {"ambient_temp": 28.5, "desc": "Céu Limpo", "rain": "Não"}
try:
    # Em produção, o backend proveria isso
    # weather_info = requests.get("http://localhost:8000/weather").json()
    pass
except: pass

c1, c2, c3 = st.columns(3)
c1.metric("Temp. Ambiente (API)", f"{weather_info['ambient_temp']} °C")
c2.metric("Previsão", weather_info['desc'])
c3.metric("Chuva Próxima?", weather_info['rain'])

st.divider()

# --- STATUS DA GERAÇÃO ---
st.subheader("📊 Comparativo de Geração")
col_p1, col_p2, col_p3 = st.columns(3)

# Dados mockados para ilustrar o cálculo de eficiência
p_main = 45.2 # Watts
p_ref = 52.8  # Watts
perda = ((p_ref - p_main) / p_ref) * 100

col_p1.metric("Painel Principal", f"{p_main} W")
col_p2.metric("Painel Referência", f"{p_ref} W")
col_p3.metric("Perda por Soiling", f"{perda:.1f}%", delta=f"{perda-5:.1f}%", delta_color="inverse")

if perda > eff_limit:
    st.warning(f"⚠️ Alerta: Perda de eficiência acima do limite de {eff_limit}%! Limpeza necessária.")

# --- GRÁFICOS ---
st.markdown("### Histórico de Eficiência vs Clima")
chart_data = pd.DataFrame({
    'Eficiência (%)': [98, 95, 92, 88, 85],
    'Temp. Painel (°C)': [26, 30, 35, 42, 45],
    'Temp. Ambiente (°C)': [25, 26, 27, 28, 28]
})
st.line_chart(chart_data)

st.divider()
st.info("💡 Dica: O sistema economiza água cancelando ciclos de limpeza se a API detectar chuva iminente.")
