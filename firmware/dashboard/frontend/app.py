import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="ASCM Smart Dashboard", layout="wide", page_icon="🌤️")

BACKEND_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 1.5
REFRESH_SECONDS = 5

# Dados exibidos quando o backend esta offline
OFFLINE_TELEMETRY = {
    "limit_home": 1,
    "limit_end": 1,
    "temperature": 0.0,
    "lux": 0.0,
    "pump": "off",
    "wiper": "stopped",
    "cleaning_active": False,
    "panel_main": {"voltage": 0.0, "current": 0.0, "power": 0.0},
    "panel_ref": {"voltage": 0.0, "current": 0.0, "power": 0.0},
}

OFFLINE_WEATHER = {
    "ambient_temp": 0.0,
    "description": "N/A",
    "is_raining": False,
    "wind_speed": 0.0,
    "humidity": 0,
}


def inject_custom_css():
    st.markdown(
        """
        <style>
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.08) 100%);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 18px 22px;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 50px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .badge-online {
            background-color: rgba(46,204,113,0.15);
            color: #2ecc71;
            border: 1px solid rgba(46,204,113,0.3);
        }
        .badge-offline {
            background-color: rgba(231,76,60,0.15);
            color: #e74c3c;
            border: 1px solid rgba(231,76,60,0.3);
        }
        .pulse-active {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 8px;
            background-color: #3498db;
            animation: pulse 1.6s infinite;
            vertical-align: middle;
        }
        @keyframes pulse {
            0%   { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52,152,219,0.7); }
            70%  { transform: scale(1);    box-shadow: 0 0 0 8px rgba(52,152,219,0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(52,152,219,0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def fetch_telemetry():
    """Busca a telemetria atual. Retorna (dados, online)."""
    try:
        resp = requests.get(f"{BACKEND_URL}/telemetry", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json(), True
    except requests.RequestException:
        pass
    return OFFLINE_TELEMETRY, False


def fetch_weather():
    try:
        resp = requests.get(f"{BACKEND_URL}/weather", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 200:
            return resp.json() or OFFLINE_WEATHER
    except requests.RequestException:
        pass
    return OFFLINE_WEATHER


def fetch_history(limit: int = 50):
    try:
        resp = requests.get(
            f"{BACKEND_URL}/history/telemetry",
            params={"limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json() or []
    except requests.RequestException:
        pass
    return []


def send_command(path: str, label: str, icon: str):
    try:
        resp = requests.post(f"{BACKEND_URL}{path}", timeout=REQUEST_TIMEOUT)
        if resp.status_code == 409:
            st.warning("Ja existe um ciclo de limpeza em andamento.")
        elif resp.status_code >= 400:
            st.error(f"O backend recusou o comando (HTTP {resp.status_code}).")
        else:
            st.toast(label, icon=icon)
    except requests.RequestException:
        st.error("Erro de comunicacao com o backend.")


# --- SIDEBAR ---
@st.fragment(run_every=REFRESH_SECONDS)
def render_sidebar_status():
    telemetry, is_online = fetch_telemetry()
    weather_data = fetch_weather()

    st.divider()
    st.header("📡 Status de Conexao")
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
        st.warning("Backend offline. Exibindo valores de fallback.")

    st.header("🔌 Status do Hardware")
    home_status = (
        "🏠 HOME (Ativado)" if telemetry.get("limit_home", 1) == 0 else "⚪ Aberto"
    )
    end_status = (
        "🏁 END (Ativado)" if telemetry.get("limit_end", 1) == 0 else "⚪ Aberto"
    )
    st.info(f"Fim de Curso Inicio: {home_status}")
    st.info(f"Fim de Curso Final: {end_status}")

    st.header("☁️ Clima Local")
    st.write(
        f"**Condicao:** {str(weather_data.get('description', 'N/A')).capitalize()}"
    )
    st.write(f"**Temp. Externa:** {weather_data.get('ambient_temp', 0.0)}°C")
    st.write(f"**Vento:** {weather_data.get('wind_speed', 0.0)} km/h")
    st.write(f"**Umidade:** {weather_data.get('humidity', 0)}%")


# --- DASHBOARD PRINCIPAL ---
@st.fragment(run_every=REFRESH_SECONDS)
def render_main_dashboard(eff_limit: float, auto_on: bool):
    telemetry, _ = fetch_telemetry()
    weather_data = fetch_weather()
    history_list = fetch_history(limit=50)

    ambient_temp = weather_data.get("ambient_temp", 0.0)
    panel_temp = telemetry.get("temperature", 0.0)

    st.title("🌤️ ASCM Smart Monitoring")

    pump_val = str(telemetry.get("pump") or "off")
    wiper_val = str(telemetry.get("wiper") or "stopped")
    active = []
    if pump_val != "off":
        active.append(
            f'<span class="pulse-active"></span><b>Bomba ativa</b> ({pump_val.upper()})'
        )
    if wiper_val != "stopped":
        active.append(
            f'<span class="pulse-active"></span><b>Rodo em movimento</b> ({wiper_val.upper()})'
        )
    if active:
        st.markdown(
            '<div style="margin-bottom:18px;font-size:1.05rem;color:#3498db;">'
            + " &nbsp;|&nbsp; ".join(active)
            + "</div>",
            unsafe_allow_html=True,
        )

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Temperatura Painel",
        f"{panel_temp} °C",
        delta=f"{panel_temp - ambient_temp:.1f}°C vs ambiente",
    )
    c2.metric("Luminosidade", f"{telemetry.get('lux', 0)} LDR")
    c3.metric(
        "Modo de Operacao",
        "Automacao Ligada" if auto_on else "Modo Manual",
        delta=f"Bomba: {pump_val.upper()} | Rodo: {wiper_val.upper()}",
        delta_color="off",
    )

    st.divider()

    st.subheader("📊 Comparativo de Geracao")
    col_p1, col_p2, col_p3 = st.columns(3)
    p_main = telemetry.get("panel_main", {}).get("power", 0.0)
    p_ref = telemetry.get("panel_ref", {}).get("power", 0.0)
    perda = ((p_ref - p_main) / p_ref * 100) if p_ref > 0 else 0.0

    col_p1.metric("Painel Principal (Sujo)", f"{p_main:.2f} W")
    col_p2.metric("Painel Referencia (Limpo)", f"{p_ref:.2f} W")
    col_p3.metric(
        "Perda por Soiling",
        f"{perda:.1f}%",
        delta=f"{perda - eff_limit:.1f}% vs limite",
        delta_color="inverse",
    )

    if perda > eff_limit:
        st.warning(
            f"⚠️ Perda de eficiencia ({perda:.1f}%) acima do limite de "
            f"{eff_limit:.1f}%! Limpeza necessaria."
        )

    st.subheader("🚀 Comandos Manuais")
    is_cleaning = bool(telemetry.get("cleaning_active", False))
    cm1, cm2, cm3, cm4 = st.columns(4)
    if cm1.button("🧼 Ciclo Completo", disabled=is_cleaning, use_container_width=True):
        send_command("/cycle/clean", "Ciclo completo disparado!", "🧼")
    if cm2.button("❄️ Arrefecer", disabled=is_cleaning, use_container_width=True):
        send_command("/cycle/cool", "Arrefecimento iniciado!", "❄️")
    if cm3.button("🏠 Ir para Home", disabled=is_cleaning, use_container_width=True):
        send_command(
            "/actuators/motor?direction=backward", "Retorno para Home enviado!", "🏠"
        )
    if cm4.button("🛑 PARAR TUDO", type="primary", use_container_width=True):
        send_command("/stop", "Parada de emergencia executada!", "🛑")

    st.divider()

    st.markdown("### Historico de Performance")
    if history_list:
        df = pd.DataFrame(history_list)
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).set_index("timestamp")

        df_power = df[["p_main_w", "p_ref_w"]].copy()
        df_power.columns = ["Painel Principal (W)", "Painel Referencia (W)"]
        st.line_chart(df_power)

        df_temp = df[["temp_c"]].copy()
        df_temp.columns = ["Temperatura do Painel (°C)"]
        st.line_chart(df_temp)
    else:
        st.info(
            "Sem leituras registradas ainda. Os graficos aparecem conforme o "
            "loop de automacao grava a telemetria."
        )


# --- LAYOUT ---
inject_custom_css()

with st.sidebar:
    st.title("⚙️ Configuracoes Smart")
    lat = st.number_input("Latitude", value=-23.1615, format="%.4f")
    lon = st.number_input("Longitude", value=-45.8485, format="%.4f")
    eff_limit = st.slider("Limiar de Sujeira (%)", 5, 30, 10)
    temp_limit = st.slider("Delta de Temperatura (°C)", 2, 10, 5)
    auto_on = st.toggle("Automacao Ativa", True)

    if st.button("Salvar Configuracoes"):
        new_cfg = {
            "latitude": float(lat),
            "longitude": float(lon),
            "efficiency_threshold": float(eff_limit),
            "temp_delta_limit": float(temp_limit),
            "automation_enabled": auto_on,
        }
        try:
            r = requests.post(
                f"{BACKEND_URL}/config/update", json=new_cfg, timeout=REQUEST_TIMEOUT
            )
            if r.status_code == 200:
                st.success("Configuracoes aplicadas!")
            else:
                st.error(f"Erro ao aplicar configuracoes (HTTP {r.status_code}).")
        except requests.RequestException:
            st.error("Erro de comunicacao com o backend.")

    render_sidebar_status()

render_main_dashboard(float(eff_limit), bool(auto_on))
