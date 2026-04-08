import requests

class WeatherService:
    def __init__(self, api_key: str = "MOCK_KEY"):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"

    def get_weather_data(self, city: str):
        """
        Busca temperatura ambiente e previsão de chuva.
        Para o protótipo, se não houver chave real, retorna dados simulados.
        """
        if self.api_key == "MOCK_KEY":
            return {
                "ambient_temp": 28.0,
                "is_raining": False,
                "will_rain_soon": False,
                "description": "Céu Limpo (Simulado)"
            }
        
        try:
            params = {"q": city, "appid": self.api_key, "units": "metric", "lang": "pt_br"}
            resp = requests.get(self.base_url, params=params, timeout=5)
            data = resp.json()
            return {
                "ambient_temp": data["main"]["temp"],
                "is_raining": "rain" in data,
                "will_rain_soon": False, # Exigiria API de forecast 5 dias
                "description": data["weather"][0]["description"]
            }
        except Exception:
            return None
