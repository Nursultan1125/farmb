#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import serial
import threading
from paho.mqtt import client as mqtt
from serial.tools import list_ports

# === Настройки MQTT ===
BROKER = "home.memorymee.org"
PORT = 1883
TOPIC_SUB = "farmbot/cmd"     # где слушаем команды
TOPIC_PUB = "farmbot/ack"     # куда публикуем ответы
CLIENT_ID = "rpi_farmbot"

# === Настройки Serial ===
SERIAL_PORT = "/dev/ttyUSB0"  # или /dev/ttyAMA0, если напрямую UART
BAUDRATE = 115200
TIMEOUT = 1.0

USERNAME = "admin"
PASSWORD = "pass12345"

# === Глобальные объекты ===
ser = None
client: serial.Serial | None = None
connected = False
stop_flag = False


# ====== MQTT callbacks ======
def on_connect(mqtt_client, userdata, flags, rc):
    global connected
    if rc == 0:
        connected = True
        print("✅ Connected to MQTT broker")
        mqtt_client.subscribe(TOPIC_SUB)
        print(f"📡 Subscribed to {TOPIC_SUB}")
    else:
        print("❌ Failed to connect, return code:", rc)


def on_message(mqtt_client, userdata, msg):
    """Вызывается при получении сообщения из MQTT"""
    try:
        payload = msg.payload.decode("utf-8")
        print(f"📨 Received: {payload}")
        data = json.loads(payload)

        if "cmd" in data:
            cmd = data["cmd"].strip()
            print(f"➡️ Sending to Arduino: {cmd}")
            ser.write((cmd + "\n").encode("utf-8"))
        else:
            print("⚠️ JSON does not contain 'cmd' field:", data)

    except json.JSONDecodeError:
        print("⚠️ Invalid JSON received:", msg.payload)
    except Exception as e:
        print("⚠️ Error handling message:", e)


def on_disconnect(mqtt_client, userdata, rc):
    global connected
    connected = False
    print("🔌 MQTT disconnected (rc =", rc, ")")


# ====== Serial listener ======
def serial_reader():
    """Отдельный поток, читающий ответы от Arduino"""
    while not stop_flag:
        try:
            if ser.in_waiting:
                line = ser.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    print(f"⬅️ From Arduino: {line}")
                    if connected:
                        client.publish(TOPIC_PUB, json.dumps({"ack": line}))
            else:
                time.sleep(0.05)
        except Exception as e:
            print("⚠️ Serial read error:", e)
            time.sleep(1)


def find_arduino_port():
    """Ищем первый доступный порт, который выглядит как Arduino"""
    ports = list_ports.comports()
    for port in ports:
        # port.device — путь, port.description — описание устройства
        if "USB" in port.device or "ACM" in port.device or "Arduino" in port.description:
            print(f"✅ Found serial port: {port.device} ({port.description})")
            return port.device
    raise RuntimeError("❌ Arduino not found! Подключите устройство и попробуйте снова.")


# ====== Главная функция ======
def main():
    global ser, client, stop_flag

    # --- Подключаем Serial ---
    print(f"🔧 Opening serial port {SERIAL_PORT} @ {BAUDRATE}...")
    ser = serial.Serial(find_arduino_port(), BAUDRATE, timeout=TIMEOUT)
    time.sleep(2)
    print("✅ Serial connected")

    # --- MQTT setup ---
    client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    print(f"🌐 Connecting to MQTT broker {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_start()

    # --- Поток для чтения из Serial ---
    t = threading.Thread(target=serial_reader, daemon=True)
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping...")
        stop_flag = True
        client.loop_stop()
        client.disconnect()
        ser.close()


if __name__ == "__main__":
    main()
