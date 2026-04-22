import requests


class WeatherService:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"

    def get_weather_data(self, lat: float = -23.1615, lon: float = -45.8485):
        """
        Busca dados meteorológicos usando a API Open-Meteo.
        Default: São José dos Campos (SJC), BR.
        """
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,surface_pressure,wind_speed_10m",
            "daily": "sunrise,sunset,temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
            "hourly": "temperature_2m,weather_code,precipitation_probability,wind_speed_10m,apparent_temperature,relative_humidity_2m,surface_pressure,visibility,cloud_cover",
            "timezone": "auto",
            "forecast_days": 7,
        }

        try:
            resp = requests.get(self.base_url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current", {})
            
            # Mapeamento simples de weather_code para descrição (WMO Weather interpretation codes)
            # 0: Sky clear, 1-3: Partly cloudy, 45-48: Fog, 51-67: Drizzle/Rain, etc.
            weather_code = current.get("weather_code", 0)
            description = self._interpret_weather_code(weather_code)

            return {
                "ambient_temp": current.get("temperature_2m"),
                "is_raining": current.get("precipitation", 0) > 0,
                "will_rain_soon": self._check_upcoming_rain(data.get("hourly", {})),
                "description": description,
                "wind_speed": current.get("wind_speed_10m"),
                "humidity": current.get("relative_humidity_2m"),
                "pressure": current.get("surface_pressure"),
            }
        except Exception as e:
            print(f"Erro ao buscar clima: {e}")
            return None

    def _interpret_weather_code(self, code: int) -> str:
        codes = {
            0: "Céu Limpo",
            1: "Principalmente Limpo",
            2: "Parcialmente Nublado",
            3: "Encoberto",
            45: "Nevoeiro",
            48: "Nevoeiro com Geada",
            51: "Garoa Leve",
            53: "Garoa Moderada",
            55: "Garoa Densa",
            61: "Chuva Leve",
            63: "Chuva Moderada",
            65: "Chuva Forte",
            80: "Pancadas de Chuva Leves",
            81: "Pancadas de Chuva Moderadas",
            82: "Pancadas de Chuva Violentas",
            95: "Trovoada",
        }
        return codes.get(code, f"Código {code}")

    def _check_upcoming_rain(self, hourly_data: dict) -> bool:
        """Verifica se há previsão de chuva nas próximas 3 horas"""
        if not hourly_data or "precipitation_probability" not in hourly_data:
            return False
        
        # Próximas 3 horas
        next_probs = hourly_data["precipitation_probability"][:3]
        return any(p > 30 for p in next_probs) # Mais de 30% de chance
