from telemetrix4arduino import telemetrix4arduino
import time

class HardwareManager:
    def __init__(self):
        self.board = telemetrix4arduino.Telemetrix4Arduino()
        
        # --- Pinos Atuadores ---
        self.PUMP_PIN = 6    # Mudado para pino PWM (~6) para controle de vazão
        self.MOTOR_IN1 = 9
        self.MOTOR_IN2 = 10
        self.MOTOR_ENA = 11  # PWM Velocidade Rodo
        
        # --- Pinos Sensores ---
        self.LIMIT_HOME = 2  # Fim de curso - Início
        self.LIMIT_END = 3   # Fim de curso - Final
        self.LDR_PIN = 0     # A0
        self.TEMP_PIN = 1    # A1
        
        self._setup_pins()

    def _setup_pins(self):
        # Atuadores
        self.board.set_pin_mode_pwm_output(self.PUMP_PIN)
        self.board.set_pin_mode_digital_output(self.MOTOR_IN1)
        self.board.set_pin_mode_digital_output(self.MOTOR_IN2)
        self.board.set_pin_mode_pwm_output(self.MOTOR_ENA)
        
        # Sensores Fim de Curso (com Pull-up interno)
        self.board.set_pin_mode_digital_input_pullup(self.LIMIT_HOME)
        self.board.set_pin_mode_digital_input_pullup(self.LIMIT_END)
        
        # Analógicos e I2C
        self.board.set_pin_mode_analog_input(self.LDR_PIN)
        self.board.set_pin_mode_analog_input(self.TEMP_PIN)
        self.board.set_pin_mode_i2c()

    def set_pump(self, flow_level: str):
        """
        flow_level: 'high' (arrefecimento), 'low' (limpeza), 'off'
        """
        if flow_level == "high":
            self.board.analog_write(self.PUMP_PIN, 255) # 100% vazão
        elif flow_level == "low":
            self.board.analog_write(self.PUMP_PIN, 80)  # ~30% vazão
        else:
            self.board.analog_write(self.PUMP_PIN, 0)

    def move_wiper(self, direction: str, speed: int = 200):
        """Move o rodo respeitando os fins de curso"""
        # Lê estado atual (0 = pressionado, 1 = solto, devido ao Pull-up)
        home = self.board.digital_read(self.LIMIT_HOME)[0]
        end = self.board.digital_read(self.LIMIT_END)[0]

        if direction == "forward" and end == 1:
            self.board.digital_write(self.MOTOR_IN1, 1)
            self.board.digital_write(self.MOTOR_IN2, 0)
            self.board.analog_write(self.MOTOR_ENA, speed)
        elif direction == "backward" and home == 1:
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
        # Retorna o estado real dos fins de curso também
        home = self.board.digital_read(self.LIMIT_HOME)
        end = self.board.digital_read(self.LIMIT_END)
        return {
            "temperature": 25.0, # Implementar lógica real do termopar/temp
            "lux": 500,
            "limit_home": home[0] if home else 1,
            "limit_end": end[0] if end else 1
        }
