import time
import sys
import os

# Adiciona o diretório atual ao path para importar o backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.hardware import HardwareManager


def test_ina():
    print("--- Teste do Sensor INA219 ---")
    print("Tentando conectar ao Arduino...")
    try:
        # Nota: O HardwareManager inicializa o Telemetrix automaticamente
        hw = HardwareManager()
    except Exception as e:
        print(f"Erro ao conectar ao Arduino: {e}")
        return

    print("Habilitando barramento I2C...")
    try:
        # Garante que o I2C está habilitado (pode já ter sido chamado no __init__ se você alterou)
        hw.board.set_pin_mode_i2c()
    except Exception as e:
        print(f"Erro ao habilitar I2C: {e}")
        hw.board.shutdown()
        return

    print("Configurando INA219 (Modo Contínuo, 16V Range para Painel 6V)...")
    try:
        # Escreve 0x199F no registrador 0x00
        # 0x199F: 16V Range, 320mV Shunt, 12-bit ADC
        hw.board.i2c_write(0x40, [0x00, 0x19, 0x9F])
        time.sleep(0.1)
    except Exception as e:
        print(f"Erro ao configurar: {e}")

    print("Iniciando leituras (Ctrl+C para parar)...")
    print("Endereço esperado: 0x40 (Painel Principal)")
    print("-----------------------------------------")

    try:
        while True:
            # Solicita leitura do registrador de voltagem (0x02) e corrente (0x01 via _read_ina219)
            hw._read_ina219(0x40)

            # Aguarda um pouco para os callbacks processarem
            time.sleep(0.5)

            data = hw.state["panel_main"]
            v = data["voltage"]
            i = data["current"]
            p = data["power"]

            print(f"[DATA] Painel: {v:5.3f}V | I: {i:6.2f}mA | P: {p:6.4f}W")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nTeste interrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro durante a execução: {e}")
    finally:
        print("Encerrando conexão com o Arduino...")
        try:
            hw.board.shutdown()
        except Exception:
            pass


if __name__ == "__main__":
    test_ina()
