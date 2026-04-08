from telemetrix import telemetrix

class HardwareManager:
    def __init__(self):
        # Inicializa a conexão com o Arduino
        # Em produção, você pode passar parâmetros como o port serial
        self.board = telemetrix.Telemetrix()
        
        # --- Pinos Atuadores ---
        self.PUMP_PIN = 6
        self.MOTOR_IN1 = 9
        self.MOTOR_IN2 = 10
        self.MOTOR_ENA = 11
        
        # --- Pinos Sensores ---
        self.LIMIT_HOME = 2
        self.LIMIT_END = 3
        self.LDR_PIN = 0     # A0
        self.TEMP_PIN = 1    # A1
        
        # Estado dos sensores (Cache atualizado via callbacks)
        self.state = {
            "limit_home": 1, # 1 = Solto (Pull-up)
            "limit_end": 1,
            "lux": 0,
            "temperature": 0.0
        }
        
        self._setup_pins()

    def _setup_pins(self):
        # Atuadores
        self.board.set_pin_mode_analog_output(self.PUMP_PIN)
        self.board.set_pin_mode_digital_output(self.MOTOR_IN1)
        self.board.set_pin_mode_digital_output(self.MOTOR_IN2)
        self.board.set_pin_mode_analog_output(self.MOTOR_ENA)
        
        # Sensores Digitais com Callback
        self.board.set_pin_mode_digital_input_pullup(self.LIMIT_HOME, callback=self._limit_home_cb)
        self.board.set_pin_mode_digital_input_pullup(self.LIMIT_END, callback=self._limit_end_cb)
        
        # Sensores Analógicos com Callback
        self.board.set_pin_mode_analog_input(self.LDR_PIN, callback=self._ldr_cb)
        self.board.set_pin_mode_analog_input(self.TEMP_PIN, callback=self._temp_cb)
        
        # I2C
        self.board.set_pin_mode_i2c()

    # --- Callbacks ---
    def _limit_home_cb(self, data):
        self.state["limit_home"] = data[2]

    def _limit_end_cb(self, data):
        self.state["limit_end"] = data[2]

    def _ldr_cb(self, data):
        self.state["lux"] = data[2]

    def _temp_cb(self, data):
        # Conversão simples de exemplo (ajustar conforme sensor real)
        raw_val = data[2]
        self.state["temperature"] = round((raw_val * 5.0 / 1023.0) * 100, 2)

    # --- Ações ---
    def set_pump(self, flow_level: str):
        if flow_level == "high":
            self.board.analog_write(self.PUMP_PIN, 255)
        elif flow_level == "low":
            self.board.analog_write(self.PUMP_PIN, 80)
        else:
            self.board.analog_write(self.PUMP_PIN, 0)

    def move_wiper(self, direction: str, speed: int = 200):
        if direction == "forward" and self.state["limit_end"] == 1:
            self.board.digital_write(self.MOTOR_IN1, 1)
            self.board.digital_write(self.MOTOR_IN2, 0)
            self.board.analog_write(self.MOTOR_ENA, speed)
        elif direction == "backward" and self.state["limit_home"] == 1:
            self.board.digital_write(self.MOTOR_IN1, 0)
            self.board.digital_write(self.MOTOR_IN2, 1)
            self.board.analog_write(self.MOTOR_ENA, speed)
        else:
            self.stop_wiper()

    def stop_wiper(self):
        self.board.digital_write(self.MOTOR_IN1, 0)
        self.board.digital_write(self.MOTOR_IN2, 0)
        self.board.analog_write(self.MOTOR_ENA, 0)

    def get_all_sensors(self):
        # Placeholder para o INA219 (seria via I2C read)
        return {
            "panel_main": {"power": 45.0}, # Mock
            "panel_ref": {"power": 50.0},  # Mock
            **self.state
        }
