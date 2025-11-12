import paho.mqtt.client as mqtt

BROKER = "home.memorymee.org"  # адрес вашего MQTT-брокера
PORT = 1883
TOPIC = "farmbot/cmd"        # топик для подписки

USERNAME = "admin"
PASSWORD = "pass12345"

# --- Callback при подключении ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to broker")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to topic: {TOPIC}")
    else:
        print("❌ Connection failed with code", rc)

# --- Callback при получении сообщения ---
def on_message(client, userdata, msg):
    print(f"📨 Received message: {msg.payload.decode()} (topic: {msg.topic})")

# --- Настройка клиента ---
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message

# --- Подключение к брокеру ---
client.connect(BROKER, PORT, 60)

# --- Запуск цикла обработки сети (блокирующий) ---
client.loop_forever()
