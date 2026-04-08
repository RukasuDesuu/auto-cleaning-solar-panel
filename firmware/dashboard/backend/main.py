from fastapi import FastAPI, BackgroundTasks
from .hardware import HardwareManager
from .services.weather import WeatherService
from .services.logger import CSVLogger
import uvicorn
import asyncio
import time

app = FastAPI(title="ASCM Backend Smart API")
hw = HardwareManager()
weather = WeatherService()
logger = CSVLogger()

# Configurações de Automação
config = {
    "city": "Sao Paulo",
    "efficiency_threshold": 10.0,
    "temp_delta_limit": 5.0,
    "automation_enabled": True
}

@app.get("/telemetry")
async def get_telemetry():
    return hw.get_all_sensors()

@app.post("/config/update")
async def update_config(new_config: dict):
    config.update(new_config)
    logger.log_event("CONFIG_UPDATE", f"Novas config: {new_config}")
    return config

@app.post("/cycle/cool")
async def start_cooling():
    hw.set_pump("high")
    logger.log_event("COOL_START", "Acionamento manual de arrefecimento")
    return {"status": "Arrefecimento iniciado"}

@app.post("/cycle/clean")
async def start_cleaning(background_tasks: BackgroundTasks):
    logger.log_event("CLEAN_START", "Iniciando ciclo completo de limpeza")
    background_tasks.add_task(run_full_clean_cycle)
    return {"status": "Ciclo de limpeza disparado"}

@app.post("/stop")
async def emergency_stop():
    hw.set_pump("off")
    hw.stop_wiper()
    logger.log_event("EMERGENCY_STOP", "Parada de emergência acionada")
    return {"status": "Parada executada"}

@app.post("/actuators/motor")
async def control_motor(direction: str, speed: int = 200):
    hw.move_wiper(direction, speed)
    return {"motor": direction}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(automation_loop())

async def automation_loop():
    """Loop de automação e logging (1 vez por minuto)"""
    while True:
        # 1. Coleta dados
        hw_data = hw.get_all_sensors()
        wt_data = weather.get_weather_data(config["city"])
        
        # 2. LOGGING: Salva telemetria no CSV
        logger.log_telemetry(hw_data)

        if config["automation_enabled"] and wt_data:
            # 3. Lógica de Arrefecimento
            if hw_data["temperature"] > (wt_data["ambient_temp"] + config["temp_delta_limit"]):
                hw.set_pump("high")
                logger.log_event("AUTO_COOL", f"Temp painel ({hw_data['temperature']}°C) acima do limite")
            else:
                hw.set_pump("off")

            # 4. Lógica de Limpeza (Simplificada)
            p_main = hw_data.get("panel_main", {}).get("power", 0)
            p_ref = hw_data.get("panel_ref", {}).get("power", 0)
            if p_ref > 0:
                diff = ((p_ref - p_main) / p_ref) * 100
                if diff > config["efficiency_threshold"] and not wt_data["is_raining"]:
                    logger.log_event("AUTO_CLEAN", f"Perda detectada ({diff:.1f}%). Iniciando limpeza.")
                    # run_full_clean_cycle() # Seria ideal via BackgroundTask

        await asyncio.sleep(60)

def run_full_clean_cycle():
    hw.set_pump("low")
    time.sleep(2)
    while hw.get_all_sensors()["limit_end"] == 1:
        hw.move_wiper("forward", 180)
        time.sleep(0.1)
    hw.stop_wiper()
    time.sleep(1)
    while hw.get_all_sensors()["limit_home"] == 1:
        hw.move_wiper("backward", 180)
        time.sleep(0.1)
    hw.stop_wiper()
    hw.set_pump("off")
    logger.log_event("CLEAN_DONE", "Ciclo de limpeza finalizado com sucesso")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
