#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tkinter as tk
from tkinter import ttk
from paho.mqtt import client as mqtt

# === MQTT настройки ===
BROKER = "home.memorymee.org"
PORT = 1883
TOPIC_CMD = "farmbot/cmd"
TOPIC_ACK = "farmbot/ack"
USERNAME = "admin"
PASSWORD = "pass12345"

# === Начальное состояние ===
position = {"X": 0.0, "Y": 0.0, "Z": 0.0}
step = 0.5     # шаг движения в мм
feedrate = 1000 # скорость подачи
ready = True   # блокируем до получения OK после G28

# === Границы ===
limits = {
    "X": (0.0, 120.0),  # min, max
    "Y": (0.0, 70.0),
    "Z": (0.0, 50.0)
}

# === MQTT клиент ===
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Подключено к MQTT брокеру")
        client.subscribe(TOPIC_ACK)
        print(f"📡 Подписка на {TOPIC_ACK}")
        # Отправляем домой при подключении
    else:
        print(f"❌ Ошибка подключения: {rc}")

def on_message(client, userdata, msg):
    global ready
    payload = json.loads(msg.payload.decode())
    print("📥 Получено:", payload)
    if payload["ack"] == "OK":
        ready = True
        lbl_status.config(text="✅ Готов к следующей команде", foreground="green")
    else:
        lbl_status.config(text=f"ℹ️ Ответ: {payload}", foreground="blue")

client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, PORT, 60)
client.loop_start()

# === Отправка G-кода ===
def send_gcode():

    cmd = f"G0 X{position['X']:.2f} Y{position['Y']:.2f} Z{position['Z']:.2f} F{feedrate}"
    message = json.dumps({"cmd": cmd})
    client.publish(TOPIC_CMD, message)
    print("📤", message)
    lbl_status.config(text=f"📤 Отправлено: {cmd}", foreground="black")

    ready = False  # блокируем отправку до OK

# === Команда домой (G28) ===
def send_home():
    global ready
    ready = False
    lbl_status.config(text="🏠 Отправка домой (G28)...", foreground="orange")
    cmd = "G28"
    message = json.dumps({"cmd": cmd})
    client.publish(TOPIC_CMD, message)
    position['X'] = 0
    position['Y'] = 0
    position['Z'] = 0
    print("📤", message)

# === Движение с проверкой границ ===
def move(axis, delta):
    global ready
    if not ready:
        lbl_status.config(text="⏳ Ожидание OK...", foreground="orange")
        print("⚠️ Ожидание OK от контроллера")
        return
    min_val, max_val = limits[axis]
    new_val = position[axis] + delta
    if new_val < min_val:
        new_val = min_val
        lbl_status.config(text=f"⚠️ {axis} достиг минимума {min_val}", foreground="red")
    elif new_val > max_val:
        new_val = max_val
        lbl_status.config(text=f"⚠️ {axis} достиг максимума {max_val}", foreground="red")
    position[axis] = new_val
    print("+++++++++++")
    send_gcode()
    update_labels()

# === Обновление меток ===
def update_labels():
    lbl_x.config(text=f"X: {position['X']:.1f}")
    lbl_y.config(text=f"Y: {position['Y']:.1f}")
    lbl_z.config(text=f"Z: {position['Z']:.1f}")

# === Управление с клавиатуры ===
def on_key(event):
    key = event.keysym
    if key == "Up":
        move("Y", step)
    elif key == "Down":
        move("Y", -step)
    elif key == "Left":
        move("X", -step)
    elif key == "Right":
        move("X", step)
    elif key == "Prior":     # PageUp
        move("Z", step)
    elif key == "Next":      # PageDown
        move("Z", -step)
    elif key == "h" or key == "H":
        send_home()

# === Интерфейс Tkinter ===
root = tk.Tk()
root.title("MQTT CNC Controller")
root.geometry("420x400")
root.resizable(False, False)

frame = ttk.Frame(root, padding=10)
frame.pack(expand=True, fill="both")

# === Координаты ===
lbl_title = ttk.Label(frame, text="Положение головки", font=("Arial", 14, "bold"))
lbl_title.pack(pady=10)

lbl_x = ttk.Label(frame, text=f"X: {position['X']}", font=("Arial", 12))
lbl_y = ttk.Label(frame, text=f"Y: {position['Y']}", font=("Arial", 12))
lbl_z = ttk.Label(frame, text=f"Z: {position['Z']}", font=("Arial", 12))

lbl_x.pack()
lbl_y.pack()
lbl_z.pack()

# === Кнопки управления ===
btn_frame = ttk.Frame(frame)
btn_frame.pack(pady=20)

btn_up = ttk.Button(btn_frame, text="↑", width=5, command=lambda: move("Y", step))
btn_down = ttk.Button(btn_frame, text="↓", width=5, command=lambda: move("Y", -step))
btn_left = ttk.Button(btn_frame, text="←", width=5, command=lambda: move("X", -step))
btn_right = ttk.Button(btn_frame, text="→", width=5, command=lambda: move("X", step))
btn_up.grid(row=0, column=1)
btn_left.grid(row=1, column=0)
btn_right.grid(row=1, column=2)
btn_down.grid(row=2, column=1)

# === Z управление ===
z_frame = ttk.Frame(frame)
z_frame.pack(pady=10)

btn_z_up = ttk.Button(z_frame, text="Z+", width=5, command=lambda: move("Z", step))
btn_z_down = ttk.Button(z_frame, text="Z-", width=5, command=lambda: move("Z", -step))
btn_z_up.grid(row=0, column=0, padx=5)
btn_z_down.grid(row=0, column=1, padx=5)

# === Кнопка домой ===
btn_home = ttk.Button(frame, text="🏠 Домой (G28)", command=send_home)
btn_home.pack(pady=10)

# === Статус ===
lbl_status = ttk.Label(frame, text="⏳ Ожидание G28...", font=("Arial", 10))
lbl_status.pack(pady=10)

# === Управление клавиатурой ===
root.bind("<KeyPress>", on_key)

update_labels()
root.mainloop()