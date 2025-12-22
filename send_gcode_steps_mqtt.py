#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RU: Отправляет G-code команды в MQTT 20 шагов с интервалом 2 секунды.
EN: Publishes G-code commands to MQTT for 20 steps every 2 seconds.

По умолчанию публикует JSON как в probs.py:
  topic: farmbot/cmd
  payload: {"cmd": "G0 X.. Y.. Z.. F.."}

Опционально ждёт ACK на farmbot/ack с payload {"ack":"OK"} перед следующим шагом.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from typing import Dict, Tuple

from paho.mqtt import client as mqtt


DEFAULT_BROKER = "home.memorymee.org"
DEFAULT_PORT = 1883
DEFAULT_TOPIC_CMD = "farmbot/cmd"
DEFAULT_TOPIC_ACK = "farmbot/ack"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "pass12345"

DEFAULT_LIMITS: Dict[str, Tuple[float, float]] = {
    "X": (0.0, 120.0),
    "Y": (0.0, 70.0),
    "Z": (0.0, 50.0),
}


@dataclass
class State:
    pos: Dict[str, float]
    ack_ok: bool = True


state = State

def _new_mqtt_client(client_id: str | None = None) -> mqtt.Client:
    """
    RU: Создаём клиента paho-mqtt совместимо с v1/v2 API.
    EN: Create a paho-mqtt client compatible with v1/v2 callback APIs.
    """
    try:
        # paho-mqtt >= 2.0
        return mqtt.Client(
            client_id=client_id or "",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        )
    except Exception:
        # paho-mqtt < 2.0
        return mqtt.Client(client_id=client_id or "")


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def main() -> int:
    def on_connect(client: mqtt.Client, userdata, flags, rc):
        if rc == 0:
            client.subscribe(DEFAULT_TOPIC_ACK)
        else:
            print(f"❌ MQTT connect failed: rc={rc}")

    def on_message(client: mqtt.Client, userdata, msg):
        if msg.topic != DEFAULT_TOPIC_ACK:
            return
        try:
            payload = json.loads(msg.payload.decode("utf-8", errors="ignore"))
        except Exception:
            return
        if payload.get("ack") == "OK":
            state.ack_ok = True

    client = _new_mqtt_client("mqtt_1")
    client.username_pw_set(DEFAULT_USERNAME, DEFAULT_PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(DEFAULT_BROKER, DEFAULT_PORT, 60)
    client.loop_start()

    try:
        if state.ack_ok:
            client.publish(DEFAULT_TOPIC_CMD, json.dumps({"cmd": "G28"}))
            state.ack_ok = False
        for j in range(7):
            x = j * 20
            for i in range(8):
                # keep stable schedule: each step at start + i*interval
                y = i * 10
                cmd = (
                    f"G0 X{x:.2f} "
                    f"Y{y:.2f} "
                    f"Z{30:.2f} "
                    f"F{int(3000)}"
                )
                message = json.dumps({"cmd": cmd}, ensure_ascii=False)
                if state.ack_ok:
                    client.publish(DEFAULT_TOPIC_CMD, message)
                    state.ack_ok = False
                while not state.ack_ok:
                    pass
                print(f"📤 step {i + 1}/6: {message}")


    finally:
        client.loop_stop()
        client.disconnect()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


