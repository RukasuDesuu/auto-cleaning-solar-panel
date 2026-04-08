import pytest
from unittest.mock import patch

# Mock Telemetrix before importing HardwareManager
with patch("telemetrix.telemetrix.Telemetrix"):
    from backend.hardware import HardwareManager


@pytest.fixture
def hardware_manager():
    with patch("telemetrix.telemetrix.Telemetrix") as mock_tmx:
        mock_instance = mock_tmx.return_value
        manager = HardwareManager()
        manager.board = mock_instance
        return manager


def test_pump_control(hardware_manager):
    hardware_manager.set_pump("high")
    hardware_manager.board.analog_write.assert_called_with(
        hardware_manager.PUMP_PIN, 255
    )


def test_motor_control_with_limit_switch(hardware_manager):
    # Simula fim de curso solto (1)
    hardware_manager._limit_end_cb([2, 3, 1, 0])
    hardware_manager.move_wiper("forward", 150)
    hardware_manager.board.digital_write.assert_any_call(hardware_manager.MOTOR_IN1, 1)

    # Simula atingir o fim de curso (0)
    hardware_manager._limit_end_cb([2, 3, 0, 0])
    hardware_manager.move_wiper("forward", 150)
    # Deve chamar stop_wiper, que faz digital_write(IN1, 0)
    hardware_manager.board.digital_write.assert_any_call(hardware_manager.MOTOR_IN1, 0)


def test_sensor_state_update(hardware_manager):
    # Simula mudança no LDR
    hardware_manager._ldr_cb([1, 0, 800, 0])
    assert hardware_manager.get_all_sensors()["lux"] == 800

    # Simula mudança na temperatura
    # (raw_val * 5.0 / 1023.0) * 100 -> (512 * 5 / 1023) * 100 ~= 250
    hardware_manager._temp_cb([1, 1, 512, 0])
    assert hardware_manager.get_all_sensors()["temperature"] > 0
