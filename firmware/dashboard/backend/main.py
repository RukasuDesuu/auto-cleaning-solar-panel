from fastapi import FastAPI, BackgroundTasks
from .hardware import HardwareManager
from .services.weather import WeatherService
from .services.logger import CSVLogger
from contextlib import asynccontextmanager
import uvicorn
import asyncio
import time
import os
import csv


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicia o loop de automação em segundo plano
    loop_task = asyncio.create_task(automation_loop())
    yield
    # Shutdown: cancela a tarefa e desliga os atuadores
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        pass

    try:
        hw.stop_wiper()
        hw.set_pump("off")
        logger.log_event("SHUTDOWN", "Servidor finalizado e atuadores desligados.")
    except Exception:
        pass


app = FastAPI(title="ASCM Backend Smart API", lifespan=lifespan)
hw = HardwareManager()
weather = WeatherService()
logger = CSVLogger()

# Configurações de Automação
config = {
    "latitude": -23.1615,
    "longitude": -45.8485,
    "efficiency_threshold": 10.0,
    "temp_delta_limit": 5.0,
    "automation_enabled": True,
}


@app.get("/telemetry")
async def get_telemetry():
    return hw.get_all_sensors()


@app.get("/history/telemetry")
async def get_telemetry_history(limit: int = 50):
    """Retorna as últimas leituras de telemetria gravadas no arquivo CSV"""
    history = []
    if not os.path.exists(logger.telemetry_file):
        return []
    try:
        with open(logger.telemetry_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                history.append(
                    {
                        "timestamp": row["timestamp"],
                        "p_main_w": float(row["p_main_w"]) if row["p_main_w"] else 0.0,
                        "p_ref_w": float(row["p_ref_w"]) if row["p_ref_w"] else 0.0,
                        "temp_c": float(row["temp_c"]) if row["temp_c"] else 0.0,
                        "lux": float(row["lux"]) if row["lux"] else 0.0,
                        "limit_home": int(row["limit_home"])
                        if row["limit_home"]
                        else 1,
                        "limit_end": int(row["limit_end"]) if row["limit_end"] else 1,
                    }
                )
    except Exception as e:
        logger.log_event("ERROR", f"Erro ao ler histórico de telemetria: {str(e)}")

    return history[-limit:]


@app.get("/weather")
async def get_weather():
    return weather.get_weather_data(
        config.get("latitude", -23.1615), config.get("longitude", -45.8485)
    )


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


@app.post("/actuators/pump")
async def control_pump(level: str):
    """Controle manual da bomba: high, low, off"""
    hw.set_pump(level)
    logger.log_event("PUMP_MANUAL", f"Bomba definida como: {level}")
    return {"pump": level}


@app.get("/sensors/temperature")
async def get_temperature():
    return {"temperature": hw.get_all_sensors()["temperature"]}


@app.get("/sensors/lux")
async def get_lux():
    return {"lux": hw.get_all_sensors()["lux"]}


@app.get("/sensors/power")
async def get_power():
    data = hw.get_all_sensors()
    return {"panel_main": data["panel_main"], "panel_ref": data["panel_ref"]}


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


async def automation_loop():
    """Loop de automação e logging (1 vez por minuto)"""
    while True:
        try:
            # 1. Coleta dados
            hw_data = hw.get_all_sensors()
            wt_data = weather.get_weather_data(
                config.get("latitude", -23.5505), config.get("longitude", -46.6333)
            )

            # 2. LOGGING: Salva telemetria no CSV
            logger.log_telemetry(hw_data)

            if config["automation_enabled"] and wt_data:
                # 3. Lógica de Arrefecimento
                if hw_data["temperature"] > (
                    wt_data["ambient_temp"] + config["temp_delta_limit"]
                ):
                    hw.set_pump("high")
                    logger.log_event(
                        "AUTO_COOL",
                        f"Temp painel ({hw_data['temperature']}°C) acima do limite",
                    )
                else:
                    # Se não estiver no ciclo de limpeza, desliga a bomba
                    # (Precisaríamos de um estado para não interferir na limpeza)
                    pass

                # 4. Lógica de Limpeza
                p_main = hw_data.get("panel_main", {}).get("power", 0)
                p_ref = hw_data.get("panel_ref", {}).get("power", 0)
                if p_ref > 0:
                    diff = ((p_ref - p_main) / p_ref) * 100
                    if (
                        diff > config["efficiency_threshold"]
                        and not wt_data["is_raining"]
                    ):
                        logger.log_event(
                            "AUTO_CLEAN",
                            f"Perda detectada ({diff:.1f}%). Iniciando limpeza.",
                        )
                        # run_full_clean_cycle()
        except Exception as e:
            logger.log_event("ERROR", f"Erro no loop de automação: {str(e)}")

        await asyncio.sleep(60)


def run_full_clean_cycle():
    try:
        hw.set_pump("low")
        time.sleep(2)

        # Avanço do rodo
        logger.log_event("CLEAN_STEP", "Iniciando avanço do rodo")
        timeout = time.time() + 30  # Proteção contra travamento
        while hw.get_all_sensors()["limit_end"] == 1 and time.time() < timeout:
            hw.move_wiper("forward", 180)
            time.sleep(0.1)

        hw.stop_wiper()
        time.sleep(1)

        # Retorno do rodo
        logger.log_event("CLEAN_STEP", "Iniciando retorno do rodo")
        timeout = time.time() + 30
        while hw.get_all_sensors()["limit_home"] == 1 and time.time() < timeout:
            hw.move_wiper("backward", 180)
            time.sleep(0.1)

        hw.stop_wiper()
        hw.set_pump("off")
        logger.log_event("CLEAN_DONE", "Ciclo de limpeza finalizado com sucesso")
    except Exception as e:
        hw.stop_wiper()
        hw.set_pump("off")
        logger.log_event("CLEAN_ERROR", f"Erro durante ciclo de limpeza: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
