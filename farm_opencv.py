import cv2
import numpy as np
import serial
import time
from serial.tools import list_ports

# === SERIAL PORT ===
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
time.sleep(2)  # ждём подключения

# === RTSP ПОТОК ===
rtsp_url = "rtsp://admin:nurs1905@192.168.1.64:554/Streaming/Channels/101"
cap = cv2.VideoCapture(rtsp_url)

# === ГРАНИЦЫ СИНЕГО ЦВЕТА ===
lower_blue = np.array([90, 70, 50])
upper_blue = np.array([130, 255, 255])

# === РАЗМЕР ЭКРАНА РОБОТА (твоя рабочая область) ===
WORK_W = 300     # мм
WORK_H = 200     # мм

# Сюда робот должен прийти, если объект в центре
CENTER_X = WORK_W / 2
CENTER_Y = WORK_H / 2

def send_gcode(x, y):
    cmd = f"G1 X{x:.1f} Y{y:.1f}\n"
    ser.write(cmd.encode())
    print("SEND:", cmd.strip())

def find_arduino_port():
    """Ищем первый доступный порт, который выглядит как Arduino"""
    ports = list_ports.comports()
    for port in ports:
        # port.device — путь, port.description — описание устройства
        if "USB" in port.device or "ACM" in port.device or "Arduino" in port.description:
            print(f"✅ Found serial port: {port.device} ({port.description})")
            return port.device
    raise RuntimeError("❌ Arduino not found! Подключите устройство и попробуйте снова.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Ошибка чтения кадра")
        break

    h, w, _ = frame.shape

    # Конвертация в HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Маска синего цвета
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Находим контуры
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Берём самый большой объект
        c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(c)

        if area > 500:  # фильтр маленьких шумов
            x, y, w_box, h_box = cv2.boundingRect(c)
            cx = x + w_box // 2
            cy = y + h_box // 2

            # рисуем
            cv2.rectangle(frame, (x, y), (x+w_box, y+h_box), (255, 0, 0), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

            # === ПЕРЕВОД ПИКСЕЛЕЙ В РАБОЧИЕ КООРДИНАТЫ ===
            rx = WORK_W * (cx / frame.shape[1])
            ry = WORK_H * (cy / frame.shape[0])

            # === ОТПРАВКА G-CODE ===
            send_gcode(rx, ry)

    cv2.imshow("Tracking", frame)
    if cv2.waitKey(1) == 27:
        break

cap.release()
ser.close()
cv2.destroyAllWindows()
