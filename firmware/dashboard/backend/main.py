from fastapi import FastAPI
from .hardware import HardwareManager
from .services.weather import WeatherService
import asyncio

app = FastAPI(title="ASCM Backend Smart API")
hw = HardwareManager()
weather = WeatherService()

# Configurações de Automação (Podem ser alteradas via API/Frontend)
config = {
    "city": "Sao Paulo",
    "efficiency_threshold": 10.0, # % de diferença para limpar
    "temp_delta_limit": 5.0,      # Graus acima do ambiente para resfriar
    "automation_enabled": True
}

@app.get("/config")
async def get_config():
    return config

@app.post("/config/update")
async def update_config(new_config: dict):
    config.update(new_config)
    return config

@app.on_event("startup")
async def startup_event():
    # Inicia o loop de monitoramento automático em segundo plano
    asyncio.create_task(automation_loop())

async def automation_loop():
    """Loop que roda a cada 1 minuto avaliando as regras de negócio"""
    while True:
        if config["automation_enabled"]:
            # 1. Coleta dados
            hw_data = hw.get_all_sensors()
            wt_data = weather.get_weather_data(config["city"])
            
            if hw_data and wt_data:
                # 2. Lógica de Arrefecimento
                # Se Temp Painel > (Temp Ambiente + Delta)
                if hw_data["temperature"] > (wt_data["ambient_temp"] + config["temp_delta_limit"]):
                    hw.set_pump("high")
                    print(f"[AUTO] Arrefecimento ativado: {hw_data['temperature']}°C")
                else:
                    hw.set_pump("off")

                # 3. Lógica de Limpeza
                # Calcula diferença % entre Painel Referência e Principal
                # Supondo que hw_data tem 'p_main' e 'p_ref' em Watts
                p_main = hw_data.get("panel_main", {}).get("power", 0)
                p_ref = hw_data.get("panel_ref", {}).get("power", 0)
                
                if p_ref > 0:
                    diff = ((p_ref - p_main) / p_ref) * 100
                    if diff > config["efficiency_threshold"]:
                        # Só limpa se NÃO estiver chovendo e NÃO houver previsão imediata
                        if not wt_data["is_raining"]:
                            print(f"[AUTO] Sujeira detectada ({diff:.1f}%). Iniciando limpeza.")
                            # Aqui chamaria a função de ciclo completo (move_wiper, etc)

        await asyncio.sleep(60) # Espera 1 minuto

# ... (Endpoints de controle manual criados anteriormente permanecem iguais)
