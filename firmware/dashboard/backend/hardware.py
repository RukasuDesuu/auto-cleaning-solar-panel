import time
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

        # Buffers para Média Móvel
        self._temp_history = []
        self._lux_history = []
        self._history_size = 50  # Janela maior para filtrar ruídos do LM35

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
        time.sleep(0.1)
        # Configura INA219 Principal (0x40): 16V Range, Continuous, 12-bit
        self.board.i2c_write(0x40, [0x00, 0x19, 0x9F])

    # --- Callbacks ---
    def _limit_home_cb(self, data):
        self.state["limit_home"] = data[2]

    def _limit_end_cb(self, data):
        self.state["limit_end"] = data[2]

    def _ldr_cb(self, data):
        raw_val = data[2]
        self._lux_history.append(raw_val)
        if len(self._lux_history) > self._history_size:
            self._lux_history.pop(0)
        avg_lux = sum(self._lux_history) / len(self._lux_history)
        self.state["lux"] = round(avg_lux, 1)

    def _temp_cb(self, data):
        raw_val = data[2]
        # Conversão para LM35 (10mV/°C)
        millivolts = (raw_val * 5000.0) / 1023.0
        current_temp = millivolts / 10.0

        # Adiciona ao histórico e mantém o tamanho da janela
        self._temp_history.append(current_temp)
        if len(self._temp_history) > self._history_size:
            self._temp_history.pop(0)

        # Calcula a média
        avg_temp = sum(self._temp_history) / len(self._temp_history)
        self.state["temperature"] = round(avg_temp, 2)

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
        """Lê dados de potência do INA219 via I2C"""
        try:
            # Pede o Shunt (0x01) e o Bus (0x02) separadamente
            self.board.i2c_read(address, 0x01, 2, self._i2c_cb)
            self.board.i2c_read(address, 0x02, 2, self._i2c_cb)
            return self.state.get("panel_main" if address == 0x40 else "panel_ref")
        except Exception:
            return {"voltage": 0, "current": 0, "power": 0}

    def _i2c_cb(self, data):
        # data format: [report_type, i2c_port, num_bytes, i2c_address, register, byte1, byte2, ..., timestamp]
        if len(data) < 7:
            return

        address = data[3]
        register = data[4]
        key = "panel_main" if address == 0x40 else "panel_ref"

        if register == 0x01:  # Shunt Voltage Register (Corrente)
            raw_shunt = (data[5] << 8) | data[6]
            if raw_shunt > 32767:
                raw_shunt -= 65536

            shunt_v_mv = raw_shunt * 0.01  # LSB = 10uV
            current_ma = shunt_v_mv / 0.1  # I = V / R(0.1 ohm)

            # Guarda temporariamente (estado bruto em mA)
            self.state[key]["current"] = round(abs(current_ma), 2)
            # Salva o shunt em mV escondido no dicionário para a soma posterior
            self.state[key]["_shunt_mv"] = shunt_v_mv

        elif register == 0x02:  # Bus Voltage Register (Tensão)
            raw_bus = (data[5] << 8) | data[6]
            bus_v = (raw_bus >> 3) * 0.004

            # Pega o shunt salvo ou assume 0 se ainda não chegou
            shunt_v_mv = self.state[key].get("_shunt_mv", 0.0)

            # Tensão Real = Bus + Queda no Shunt
            total_v = bus_v + (shunt_v_mv / 1000.0)

            self.state[key]["voltage"] = round(total_v, 3)

            # A potência é calculada sempre que a tensão atualiza
            current_ma = self.state[key].get("current", 0.0)
            self.state[key]["power"] = round(total_v * (current_ma / 1000.0), 3)

    def get_all_sensors(self):
        # Atualiza leituras I2C (dispara pedidos)
        self._read_ina219(0x40)
        # self._read_ina219(0x41)  # Reservado para painel de referência

        return self.state
