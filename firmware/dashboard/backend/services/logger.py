import csv
import os
from datetime import datetime


class CSVLogger:
    def __init__(self, directory="logs"):
        self.directory = directory
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

        self.telemetry_file = os.path.join(self.directory, "telemetry_history.csv")
        self.events_file = os.path.join(self.directory, "events_history.csv")
        self._setup_headers()

    def _setup_headers(self):
        # Header para Telemetria
        if not os.path.exists(self.telemetry_file):
            with open(self.telemetry_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "p_main_w",
                        "p_ref_w",
                        "temp_c",
                        "lux",
                        "limit_home",
                        "limit_end",
                    ]
                )

        # Header para Eventos
        if not os.path.exists(self.events_file):
            with open(self.events_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "event_type", "description"])

    def log_telemetry(self, data):
        """Registra uma linha de dados dos sensores"""
        with open(self.telemetry_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    data.get("panel_main", {}).get("power", 0),
                    data.get("panel_ref", {}).get("power", 0),
                    data.get("temperature", 0),
                    data.get("lux", 0),
                    data.get("limit_home", 1),
                    data.get("limit_end", 1),
                ]
            )

    def log_event(self, event_type, description):
        """Registra um evento (ex: 'CLEAN_START', 'COOL_STOP')"""
        with open(self.events_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), event_type, description]
            )
