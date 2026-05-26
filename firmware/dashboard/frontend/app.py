import streamlit as st
import requests
import pandas as pd

# 1. Configuração da página e visual
st.set_page_config(page_title="ASCM Smart Dashboard", layout="wide", page_icon="🌤️")

BACKEND_URL = "http://localhost:8000"

# Fallback telemetry when backend is offline
OFFLINE_TELEMETRY = {
    "limit_home": 1,
    "limit_end": 1,
    "temperature": 0.0,
    "lux": 0.0,
    "pump": "off",
    "wiper": "stopped",
    "panel_main": {"voltage": 0.0, "current": 0.0, "power": 0.0},
    "panel_ref": {"voltage": 0.0, "current": 0.0, "power": 0.0},
}

# Fallback weather when backend is offline
OFFLINE_WEATHER = {
    "ambient_temp": 24.5,
    "description": "Céu Limpo (Demonstração)",
    "is_raining": False,
    "wind_speed": 12.0,
    "humidity": 60,
}

# 2. Injetar CSS customizado com visual premium (gradientes, glassmorphism, etc.)
def inject_custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Fonte Global */
        html, body, [class*="css"], .stApp {
            font-family: 'Inter', sans-serif;
        }

        /* Efeito Glassmorphism nos Cards de Métricas */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.08) 100%);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 20px 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
            transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        }
        
        div[data-testid="stMetric"]:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 255, 255, 0.25);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.35);
        }

        /* Botões customizados */
        .stButton>button {
            border-radius: 10px;
            padding: 10px 20px;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.1);
            background: rgba(255, 255, 255, 0.05);
            transition: all 0.2s ease-in-out;
        }
        
        .stButton>button:hover {
            background: rgba(255, 255, 255, 0.15) !important;
            border-color: rgba(255, 255, 255, 0.3) !important;
            transform: translateY(-1px);
        }

        /* Status Dot */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        .badge-online {
            background-color: rgba(46, 204, 113, 0.15);
            color: #2ecc71;
            border: 1px solid rgba(46, 204, 113, 0.3);
        }

        .badge-offline {
            background-color: rgba(231, 76, 60, 0.15);
            color: #e74c3c;
            border: 1px solid rgba(231, 76, 60, 0.3);
        }

        /* Indicadores Pulsantes para Estados Ativos */
        .pulse-active {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            background-color: #3498db;
            box-shadow: 0 0 0 0 rgba(52, 152, 219, 0.7);
            animation: pulse 1.6s infinite;
            vertical-align: middle;
        }

        .pulse-warning {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            background-color: #f1c40f;
            box-shadow: 0 0 0 0 rgba(241, 196, 15, 0.7);
            animation: pulse-warn 1.6s infinite;
            vertical-align: middle;
        }

        @keyframes pulse {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(52, 152, 219, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 8px rgba(52, 152, 219, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(52, 152, 219, 0);
            }
        }

        @keyframes pulse-warn {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(241, 196, 15, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 8px rgba(241, 196, 15, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(241, 196, 15, 0);
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_custom_css()


# --- FRAGMENTOS DE ATUALIZAÇÃO ---

# Fragmento 1: Status na Barra Lateral
@st.fragment(run_every=5)
def render_sidebar_status():
    try:
        resp = requests.get(f"{BACKEND_URL}/telemetry", timeout=1.2)
        if resp.status_code == 200:
            is_online = True
            telemetry = resp.json()
        else:
            is_online = False
            telemetry = OFFLINE_TELEMETRY
    except Exception:
        is_online = False
        telemetry = OFFLINE_TELEMETRY

    try:
        resp_wt = requests.get(f"{BACKEND_URL}/weather", timeout=1.2)
        weather_data = resp_wt.json() if resp_wt.status_code == 200 else OFFLINE_WEATHER
    except Exception:
        weather_data = OFFLINE_WEATHER

    ambient_temp = weather_data.get("ambient_temp", 0.0)
    description = weather_data.get("description", "N/A")
    wind_speed = weather_data.get("wind_speed", 0.0)
    humidity = weather_data.get("humidity", 0.0)

    st.divider()
    st.header("📡 Status de Conexão")
    if is_online:
        st.markdown(
            '<div class="status-badge badge-online">🟢 API Conectada</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="status-badge badge-offline">🔴 API Desconectada</div>',
            unsafe_allow_html=True,
        )
        st.warning("O backend está offline. Exibindo dados de fallback.")

    st.header("🔌 Status do Hardware")
    home_status = "🏠 HOME (Ativo)" if telemetry.get("limit_home", 1) == 0 else "⚪ Aberto"
    end_status = "🏁 END (Ativo)" if telemetry.get("limit_end", 1) == 0 else "⚪ Aberto"
    st.info(f"Fim de Curso Início: {home_status}")
    st.info(f"Fim de Curso Final: {end_status}")
    
    st.header("☁️ Clima Local")
    st.write(f"**Condição:** {str(description).capitalize()}")
    st.write(f"**Temp. Externa:** {ambient_temp}°C")
    st.write(f"**Vento:** {wind_speed} km/h")
    st.write(f"**Umidade:** {humidity}%")


# Fragmento 2: Área Principal do Dashboard
@st.fragment(run_every=5)
def render_main_dashboard():
    try:
        resp = requests.get(f"{BACKEND_URL}/telemetry", timeout=1.2)
        telemetry = resp.json() if resp.status_code == 200 else OFFLINE_TELEMETRY
    except Exception:
        telemetry = OFFLINE_TELEMETRY

    try:
        resp_wt = requests.get(f"{BACKEND_URL}/weather", timeout=1.2)
        weather_data = resp_wt.json() if resp_wt.status_code == 200 else OFFLINE_WEATHER
    except Exception:
        weather_data = OFFLINE_WEATHER

    ambient_temp = weather_data.get("ambient_temp", 0.0)

    try:
        resp_hist = requests.get(f"{BACKEND_URL}/history/telemetry?limit=50", timeout=1.2)
        history_list = resp_hist.json() if resp_hist.status_code == 200 else []
    except Exception:
        history_list = []

    # Cabeçalho do Dashboard
    st.title("🌤️ ASCM Smart Monitoring")
    
    # Exibir indicadores pulsantes de status ativo
    active_statuses = []
    pump_val = str(telemetry.get("pump") or "off")
    wiper_val = str(telemetry.get("wiper") or "stopped")
    
    if pump_val != "off":
        active_statuses.append(
            f'<span class="pulse-active"></span><b>Bomba ativa</b> ({pump_val.upper()})'
        )
    if wiper_val != "stopped":
        active_statuses.append(
            f'<span class="pulse-active"></span><b>Rodo em movimento</b> ({wiper_val.upper()})'
        )
    
    if active_statuses:
        status_html = " &nbsp;&nbsp;|&nbsp;&nbsp; ".join(active_statuses)
        st.markdown(f'<div style="margin-bottom: 20px; font-size: 1.1rem; color: #3498db;">{status_html}</div>', unsafe_allow_html=True)
    
    # Grid de métricas de sensores principais
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Temperatura do Painel",
        f"{telemetry['temperature']} °C",
        delta=f"{telemetry['temperature'] - ambient_temp:.1f}°C vs Ambiente",
    )
    c2.metric("Luminosidade", f"{telemetry['lux']} LDR")
    
    # Status de Automação / Atuadores
    auto_status_label = "Automação Ligada" if auto_on else "Modo Manual"
    pump_label = pump_val.upper()
    wiper_label = wiper_val.upper()
    c3.metric(
        "Modo de Operação", 
        auto_status_label, 
        delta=f"Bomba: {pump_label} | Rodo: {wiper_label}",
        delta_color="normal"
    )

    st.divider()

    # Comparativo de Geração
    st.subheader("📊 Comparativo de Geração")
    col_p1, col_p2, col_p3 = st.columns(3)

    p_main = telemetry["panel_main"]["power"]
    p_ref = telemetry["panel_ref"]["power"]
    perda = ((p_ref - p_main) / p_ref * 100) if p_ref > 0 else 0.0

    col_p1.metric("Painel Principal (Sujo)", f"{p_main:.2f} W")
    col_p2.metric("Painel Referência (Limpo)", f"{p_ref:.2f} W")
    col_p3.metric(
        "Perda por Soiling",
        f"{perda:.1f}%",
        delta=f"{perda - eff_limit:.1f}% vs Limite",
        delta_color="inverse",
    )

    # Alerta se a perda de eficiência superar o limite configurado
    if perda > eff_limit:
        st.markdown(
            f'<div style="padding: 15px; border-radius: 10px; background-color: rgba(241, 196, 15, 0.1); border: 1px solid rgba(241, 196, 15, 0.3); color: #f1c40f; margin-bottom: 20px;">'
            f'<span class="pulse-warning"></span><b>Atenção:</b> Perda de eficiência por sujeira ({perda:.1f}%) superou o limite estipulado de {eff_limit:.1f}%. Ciclo de limpeza recomendado!'
            f'</div>',
            unsafe_allow_html=True
        )

    # Controles Manuais
    st.subheader("🚀 Comandos Manuais")
    cm1, cm2, cm3, cm4 = st.columns(4)
    
    # Mapeando cliques de botões para chamadas de API do Backend
    if cm1.button("🧼 Ciclo Completo", use_container_width=True):
        try:
            requests.post(f"{BACKEND_URL}/cycle/clean", timeout=1.5)
            st.toast("Ciclo completo disparado com sucesso!", icon="🧼")
        except Exception:
            st.error("Erro ao enviar comando para o backend.")
            
    if cm2.button("❄️ Arrefecer", use_container_width=True):
        try:
            requests.post(f"{BACKEND_URL}/cycle/cool", timeout=1.5)
            st.toast("Ciclo de arrefecimento iniciado!", icon="❄️")
        except Exception:
            st.error("Erro ao enviar comando para o backend.")
            
    if cm3.button("🏠 Ir para Home", use_container_width=True):
        try:
            requests.post(f"{BACKEND_URL}/actuators/motor?direction=backward", timeout=1.5)
            st.toast("Comando para retornar à Home enviado!", icon="🏠")
        except Exception:
            st.error("Erro ao enviar comando para o backend.")
            
    if cm4.button("🛑 PARAR TUDO", type="primary", use_container_width=True):
        try:
            requests.post(f"{BACKEND_URL}/stop", timeout=1.5)
            st.toast("Parada de emergência executada!", icon="🛑")
        except Exception:
            st.error("Erro ao enviar comando de emergência.")

    st.divider()

    # Seção de histórico e gráficos dinâmicos
    st.markdown("### Histórico de Performance Real")
    
    if history_list and len(history_list) > 0:
        df = pd.DataFrame(history_list)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        
        df_chart = df[["p_main_w", "p_ref_w"]].copy()
        df_chart.columns = ["Painel Principal (W)", "Painel Referência (W)"]
        st.line_chart(df_chart)
        
        df_temp = df[["temp_c"]].copy()
        df_temp.columns = ["Temperatura do Painel (°C)"]
        st.line_chart(df_temp)
    else:
        st.info("Aguardando mais leituras no arquivo de logs para gerar os gráficos de histórico...")
        fallback_data = pd.DataFrame(
            {
                "Painel Principal (W)": [18.1, 18.2, 18.5, 18.4, 18.5],
                "Painel Referência (W)": [19.0, 19.1, 19.2, 19.1, 19.3],
            }
        )
        st.line_chart(fallback_data)


# --- LAYOUT PRINCIPAL ---

# Renderização do Sidebar Estático e chamada do Fragmento do Sidebar
with st.sidebar:
    st.title("⚙️ Configurações Smart")
    lat = st.number_input("Latitude", value=-23.1615, format="%.4f")
    lon = st.number_input("Longitude", value=-45.8485, format="%.4f")
    eff_limit = st.slider("Limiar de Sujeira (%)", 5, 30, 10)
    temp_limit = st.slider("Delta de Temperatura (°C)", 2, 10, 5)
    auto_on = st.toggle("Automação Ativa", True)

    if st.button("Salvar Configurações"):
        new_cfg = {
            "latitude": float(lat),
            "longitude": float(lon),
            "efficiency_threshold": float(eff_limit),
            "temp_delta_limit": float(temp_limit),
            "automation_enabled": auto_on,
        }
        try:
            r = requests.post(f"{BACKEND_URL}/config/update", json=new_cfg, timeout=1.5)
            if r.status_code == 200:
                st.success("Configurações aplicadas!")
            else:
                st.error("Erro ao aplicar configurações.")
        except Exception:
            st.error("Erro de comunicação com o backend.")

    # Executa a renderização dinâmica dentro do sidebar
    render_sidebar_status()

# Executa a renderização do Dashboard Principal
render_main_dashboard()
