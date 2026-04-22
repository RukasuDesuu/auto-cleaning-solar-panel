from telemetrix import telemetrix


class HardwareManager:
    def __init__(self):
        # Inicializa a conexão com o Arduino
        self.board = telemetrix.Telemetrix()

        # --- Pinos Atuadores ---
        self.PUMP_ENB = 6
        self.PUMP_IN3 = 7
        self.PUMP_IN4 = 8
        self.MOTOR_IN1 = 9
        self.MOTOR_IN2 = 10
        self.MOTOR_ENA = 11

        # --- Pinos Sensores ---
        self.LIMIT_HOME = 2
        self.LIMIT_END = 3
        self.LDR_PIN = 0  # A0
        self.TEMP_PIN = 1  # A1

        # Estado dos sensores (Cache atualizado via callbacks)
        self.state = {
            "limit_home": 1,
            "limit_end": 1,
            "lux": 0,
            "temperature": 0.0,
            "panel_main": {"voltage": 0.0, "current": 0.0, "power": 0.0},
            "panel_ref": {"voltage": 0.0, "current": 0.0, "power": 0.0},
        }

        self._setup_pins()

    def _setup_pins(self):
        # Atuadores - Wiper
        self.board.set_pin_mode_digital_output(self.MOTOR_IN1)
        self.board.set_pin_mode_digital_output(self.MOTOR_IN2)
        self.board.set_pin_mode_analog_output(self.MOTOR_ENA)

        # Atuadores - Bomba
        self.board.set_pin_mode_digital_output(self.PUMP_IN3)
        self.board.set_pin_mode_digital_output(self.PUMP_IN4)
        self.board.set_pin_mode_analog_output(self.PUMP_ENB)

        # Sensores Digitais com Callback
        self.board.set_pin_mode_digital_input_pullup(
            self.LIMIT_HOME, callback=self._limit_home_cb
        )
        self.board.set_pin_mode_digital_input_pullup(
            self.LIMIT_END, callback=self._limit_end_cb
        )

        # Sensores Analógicos com Callback
        self.board.set_pin_mode_analog_input(self.LDR_PIN, callback=self._ldr_cb)
        self.board.set_pin_mode_analog_input(self.TEMP_PIN, callback=self._temp_cb)

        # I2C para INA219
        self.board.set_pin_mode_i2c()
        # Inicia leitura contínua dos INA219 (0x40 e 0x41)
        # O INA219 exige leitura de múltiplos registradores, simplificaremos via polling no get_sensors ou callback se suportado
        # Por simplicidade com Telemetrix puro, vamos configurar um report de I2C se disponível ou ler sob demanda

    # --- Callbacks ---
    def _limit_home_cb(self, data):
        self.state["limit_home"] = data[2]

    def _limit_end_cb(self, data):
        self.state["limit_end"] = data[2]

    def _ldr_cb(self, data):
        self.state["lux"] = data[2]

    def _temp_cb(self, data):
        raw_val = data[2]
        # Conversão para LM35 (10mV/°C) ou similar
        millivolts = (raw_val * 5000.0) / 1023.0
        self.state["temperature"] = round(millivolts / 10.0, 2)

    # --- Ações ---
    def set_pump(self, flow_level: str):
        if flow_level in ["high", "low"]:
            speed = 255 if flow_level == "high" else 150
            self.board.digital_write(self.PUMP_IN3, 1)
            self.board.digital_write(self.PUMP_IN4, 0)
            self.board.analog_write(self.PUMP_ENB, speed)
        else:
            self.board.digital_write(self.PUMP_IN3, 0)
            self.board.digital_write(self.PUMP_IN4, 0)
            self.board.analog_write(self.PUMP_ENB, 0)

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

    def _read_ina219(self, address):
        """Lê dados básicos de potência do INA219 via I2C"""
        try:
            # Registrador 0x02 é o Bus Voltage
            # Registrador 0x03 é Power (requer calibração prévia no 0x05)
            # Para este exemplo, faremos uma leitura simples de tensão
            self.board.i2c_read(address, 0x02, 2, self._i2c_cb)
            # Nota: O Telemetrix é assíncrono, o valor real virá no callback
            # Em uma implementação robusta, esperaríamos ou usaríamos o cache
            return self.state.get("panel_main" if address == 0x40 else "panel_ref")
        except:
            return {"voltage": 0, "current": 0, "power": 0}

    def _i2c_cb(self, data):
        # data format: [report_type, i2c_address, register, num_bytes, byte1, byte2, ...]
        if len(data) < 6:
            return
            
        address = data[1]
        register = data[2]
        
        if register == 0x02:  # Bus Voltage Register
            # Valor bruto de 16 bits (Big Endian)
            raw_val = (data[4] << 8) | data[5]
            # No INA219, os bits de tensão estão do bit 3 ao 15 (shift right 3)
            # E cada unidade representa 4mV
            voltage_v = (raw_val >> 3) * 0.004
            
            key = "panel_main" if address == 0x40 else "panel_ref"
            self.state[key]["voltage"] = round(voltage_v, 2)
            # Mock para corrente e potência baseado na tensão e carga de 33 ohms (V = R * I)
            self.state[key]["current"] = round(voltage_v / 33.0, 3)
            self.state[key]["power"] = round(voltage_v * self.state[key]["current"], 2)

    def get_all_sensors(self):
        # Atualiza leituras I2C (dispara pedidos)
        self._read_ina219(0x40)
        self._read_ina219(0x41)
        
        return self.state
