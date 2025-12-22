#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import serial
from serial.tools import list_ports
from typing import Optional

# === Настройки Serial ===
SERIAL_PORT = "/dev/ttyUSB0"  # или /dev/ttyAMA0, если напрямую UART
BAUDRATE = 115200
TIMEOUT = 1.0

# === Глобальные объекты ===
ser: Optional[serial.Serial] = None




def find_arduino_port():
    """Ищем первый доступный порт, который выглядит как Arduino"""
    ports = list_ports.comports()
    for port in ports:
        # port.device — путь, port.description — описание устройства
        if "USB" in port.device or "ACM" in port.device or "Arduino" in port.description:
            print(f"✅ Found serial port: {port.device} ({port.description})")
            return port.device
    raise RuntimeError("❌ Arduino not found! Подключите устройство и попробуйте снова.")

def read_until_ok(ser: serial.Serial, timeout_s: float = 10.0) -> str:
    """
    RU: Ждём ответ 'ok' от Arduino/прошивки (GRBL/Marlin style).
    EN: Wait for 'ok' from Arduino firmware (GRBL/Marlin style).
    """
    deadline = time.monotonic() + timeout_s
    last_line = ""
    while time.monotonic() < deadline:
        raw = ser.readline()  # respects TIMEOUT
        if not raw:
            continue
        line = raw.decode("utf-8", errors="ignore").strip()
        if not line:
            continue
        last_line = line
        print("📥", line)
        if line.lower() == "ok" or line.lower().startswith("ok"):
            return line
    raise TimeoutError(f"Timeout waiting for 'ok'. Last line: {last_line!r}")

def send_gcode_and_wait_ok(ser: serial.Serial, cmd: str, timeout_s: float = 50.0) -> None:
    """
    RU: Отправляем G-code строку и ждём 'ok'.
    EN: Send one G-code line and wait for 'ok'.
    """
    line = cmd.strip()
    if not line:
        return
    ser.write((line + "\n").encode("utf-8"))
    ser.flush()
    print("📤", line)
    read_until_ok(ser, timeout_s=timeout_s)


# ====== Главная функция ======
def main():
    global ser

    # --- Подключаем Serial ---
    print(f"🔧 Opening serial port {SERIAL_PORT} @ {BAUDRATE}...")
    ser = serial.Serial(find_arduino_port(), BAUDRATE, timeout=TIMEOUT)
    time.sleep(2)
    print("✅ Serial connected")

    try:
        ser.reset_input_buffer()
    except Exception:
        pass

    send_gcode_and_wait_ok(ser, "G28")
    for j in range(7):
        x = j * 20
        for i in range(8):
            y = i * 10
            cmd = (
                f"G0 X{x:.2f} "
                f"Y{y:.2f} "
                f"Z{30:.2f} "
                f"F{int(3000)}"
            )
            send_gcode_and_wait_ok(ser, cmd, timeout_s=50.0)
            # Если нужно строго каждые 2 секунды (дополнительно к ожиданию 'ok'):
            # time.sleep(2)

if __name__ == "__main__":
    main()
