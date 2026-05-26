import time
from telemetrix import telemetrix

def scan_i2c():
    print("--- Scanner I2C ---")
    board = telemetrix.Telemetrix()
    
    try:
        board.set_pin_mode_i2c()
        time.sleep(1)
        
        print("Escaneando endereços de 0x01 a 0x7F...")
        found_any = False
        
        for address in range(1, 128):
            # Tenta ler 1 byte de cada endereço
            # Se o dispositivo responder, o Telemetrix não deve dar erro imediato
            # (embora o callback seja assíncrono, estamos apenas testando a presença)
            try:
                # No Telemetrix, i2c_read dispara o pedido. 
                # Se o dispositivo não existir, o Arduino pode reportar um erro ou apenas não responder.
                # Uma forma melhor de escanear no Telemetrix é observar erros no log ou usar uma função específica se houver.
                # Como não há 'i2c_scan' nativo simples que retorne lista imediata, 
                # vamos tentar ler o registro de identificação do INA219 se soubermos qual é.
                # O INA219 não tem um 'Who am I', mas o registro 0x00 é o Configuration.
                board.i2c_read(address, 0x00, 2, lambda data: print(f"Dispositivo encontrado no endereço: {hex(data[1])}"))
                time.sleep(0.05)
            except:
                pass
        
        print("Escaneamento finalizado. Aguardando 2 segundos por respostas...")
        time.sleep(2)
        
    except Exception as e:
        print(f"Erro: {e}")
    finally:
        board.shutdown()

if __name__ == "__main__":
    scan_i2c()
