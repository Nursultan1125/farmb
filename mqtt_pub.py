#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time
import signal
from paho.mqtt import client as mqtt

BROKER = "home.memorymee.org"   # адрес брокера
PORT = 1883
CLIENT_ID = "farmbot"
USERNAME = "admin"
PASSWORD = "pass12345"
TOPIC_SUB = "farmbot/pub"
TOPIC_PUB = "farmbot/cmd"


keep_running = True

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    if rc == 0:
        client.subscribe(TOPIC_SUB)
        # опционально: отправить initial status
        client.publish(TOPIC_PUB, payload="online", qos=1, retain=True)
    else:
        print("Bad connection. RC:", rc)

def on_message(client, userdata, msg):
    print(f"Message received: topic={msg.topic} payload={msg.payload!r}")
    # пример: ответ на команду
    if msg.topic.endswith("/cmd"):
        payload = msg.payload.decode(errors="ignore")
        # здесь можно разобрать gcode/команду и выполнить действие
        print("Handle command:", payload)
        # отправим подтверждение
        client.publish(f"{msg.topic.replace('/cmd','/ack')}", f"ok:{payload}", qos=1)

def on_disconnect(client, userdata, rc):
    print("Disconnected, rc=", rc)
    # при rc!=0 произошло нештатное отключение — paho попробует переподключить если loop_start используется

def on_publish(client, userdata, mid):
    print("Published message id:", mid)

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed:", mid, granted_qos)

def signal_handler(sig, frame):
    global keep_running
    print("Stopping...")
    keep_running = False

def main():
    global keep_running
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    client.username_pw_set(USERNAME, PASSWORD)

    client.connect(BROKER, PORT)


    client.publish(TOPIC_PUB, payload=json.dumps({"cmd": "G0 X0 Y1 Z1"}), qos=0, retain=False)
    print(json.dumps({"cmd": "G0 X1 Y1 Z1"}))
    print("OK")


if __name__ == "__main__":
    main()
