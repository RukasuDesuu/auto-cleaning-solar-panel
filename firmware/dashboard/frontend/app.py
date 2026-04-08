import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="ASCM Smart Dashboard", layout="wide", page_icon="🌤️")

# --- SIDEBAR: CONFIGURAÇÕES E STATUS ---
st.sidebar.title("⚙️ Configurações Smart")
city = st.sidebar.text_input("Localização (Cidade)", "Sao Paulo")
eff_limit = st.sidebar.slider("Limiar de Sujeira (%)", 5, 30, 10)
temp_limit = st.sidebar.slider("Delta de Temperatura (°C)", 2, 10, 5)
auto_on = st.sidebar.toggle("Automação Ativa", True)

if st.sidebar.button("Salvar Configurações"):
    new_cfg = {
        "city": city, "efficiency_threshold": float(eff_limit),
        "temp_delta_limit": float(temp_limit), "automation_enabled": auto_on
    }
    try:
        requests.post("http://localhost:8000/config/update", json=new_cfg, timeout=1)
        st.sidebar.success("Configurações aplicadas!")
    except:
        st.sidebar.error("Erro ao salvar config.")

# Coleta de dados reais para a Sidebar
try:
    resp = requests.get("http://localhost:8000/telemetry", timeout=1)
    telemetry = resp.json()
except:
    telemetry = {"limit_home": 1, "limit_end": 1, "temperature": 0, "lux": 0, "panel_main": {"power": 0}, "panel_ref": {"power": 0}}

st.sidebar.divider()
st.sidebar.header("📡 Status do Hardware")
home_status = "🏠 HOME (Ativado)" if telemetry["limit_home"] == 0 else "⚪ Aberto"
end_status = "🏁 END (Ativado)" if telemetry["limit_end"] == 0 else "⚪ Aberto"
st.sidebar.info(f"Fim de Curso Início: {home_status}")
st.sidebar.info(f"Fim de Curso Final: {end_status}")

# --- CABEÇALHO ---
st.title("🌤️ ASCM Smart Monitoring")
c1, c2, c3 = st.columns(3)
# Simulação de clima (pode ser expandido no backend)
c1.metric("Temperatura Painel", f"{telemetry['temperature']} °C")
c2.metric("Luminosidade", f"{telemetry['lux']} LDR")
c3.metric("Bomba/Rodo", "Ativo" if auto_on else "Manual")

st.divider()

# --- STATUS DA GERAÇÃO ---
st.subheader("📊 Comparativo de Geração")
col_p1, col_p2, col_p3 = st.columns(3)

p_main = telemetry["panel_main"]["power"]
p_ref = telemetry["panel_ref"]["power"]
perda = ((p_ref - p_main) / p_ref * 100) if p_ref > 0 else 0

col_p1.metric("Painel Principal", f"{p_main} W")
col_p2.metric("Painel Referência", f"{p_ref} W")
col_p3.metric("Perda por Soiling", f"{perda:.1f}%", delta=f"{perda-eff_limit:.1f}%", delta_color="inverse")

if perda > eff_limit:
    st.warning(f"⚠️ Alerta: Perda de eficiência acima do limite de {eff_limit}%! Limpeza necessária.")

# --- CONTROLES MANUAIS ---
st.subheader("🚀 Comandos Manuais")
cm1, cm2, cm3, cm4 = st.columns(4)
if cm1.button("🧼 Ciclo Completo"): requests.post("http://localhost:8000/cycle/clean")
if cm2.button("❄️ Arrefecer"): requests.post("http://localhost:8000/cycle/cool")
if cm3.button("🏠 Ir para Home"): requests.post("http://localhost:8000/actuators/motor?direction=backward")
if cm4.button("🛑 PARAR TUDO", type="primary"): requests.post("http://localhost:8000/stop")

st.divider()
# --- GRÁFICOS ---
st.markdown("### Histórico de Performance")
chart_data = pd.DataFrame({
    'Painel Principal': [18.1, 18.2, 18.5, 18.4, 18.5],
    'Painel Referência': [19.0, 19.1, 19.2, 19.1, 19.3]
})
st.line_chart(chart_data)
