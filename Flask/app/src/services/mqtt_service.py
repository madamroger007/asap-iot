import paho.mqtt.client as paho
from paho import mqtt
import os
import time
from datetime import datetime, timedelta
import ssl
import certifi
from dotenv import load_dotenv
from app import socketio  # Untuk emit ke client
from app.src.services.notification_service import notify_sensor_data_Service
from app.src.repositories.data_sensor_repositories import create_data_sensor_repository

# Load ENV
load_dotenv()

# Konfigurasi MQTT
BROKER = os.environ.get('MQTT_BROKER', '')
PORT = 8883
USERNAME = os.environ.get('MQTT_USERNAME')
PASSWORD = os.environ.get('MQTT_PASSWORD')
FLASK_URL = os.environ.get('FLASK_URL')

# Topik MQTT
TOPICS = [
    ("kebakaran/suhu", 1),
    ("kebakaran/asap", 1),
    ("kebakaran/api", 1),
    ("kebakaran/status", 1),
]

# Data terbaru
latest_sensor_data = {
    "SUHU": None,
    "ASAP": None,
    "API": None,
    "STATUS_KEBAKARAN": None
}

sensor_last_seen = {k: None for k in latest_sensor_data}
sensor_last_value = {k: None for k in latest_sensor_data}
sensor_last_change = {k: None for k in latest_sensor_data}
sensor_alert_sent = {k: False for k in latest_sensor_data}

last_fire_status_logged = None  # waktu terakhir simpan status kebakaran
FIRE_LOG_COOLDOWN_SECONDS = 180  # 3 menit

# Parameter
check_times = [1, 5, 15, 24]
SENSOR_RESET_HOURS = 24
SENSOR_STALE_SECONDS = 60

client = None
app_context = None

# MQTT CONNECT
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Terhubung ke MQTT Broker")
        print(f" enviroment: {os.environ.get('MQTT_BROKER')}")
        for topic, qos in TOPICS:
            client.subscribe(topic, qos)
            print(f"📡 Subscribed: {topic}")
    else:
        print(f"❌ Gagal koneksi MQTT, kode: {rc}")

# MQTT MESSAGE HANDLER
def handle_sensor_data_factory(app_context_data):
    def handle_sensor_data(client, userdata, msg):
        global last_fire_status_logged

        topic = msg.topic
        value = msg.payload.decode('utf-8').strip()

        # Mapping topik MQTT ke label internal
        mapping = {
            "kebakaran/suhu": "SUHU",
            "kebakaran/asap": "ASAP",
            "kebakaran/api": "API",
            "kebakaran/status": "STATUS_KEBAKARAN"
        }

        label = mapping.get(topic)
        if not label:
            return

        # Konversi nilai dari string ke float, dengan dukungan 'true'/'false'
        try:
            if value.lower() == "true":
                value_float = 1.0
            elif value.lower() == "false":
                value_float = 0.0
            else:
                value_float = float(value)
        except ValueError:
            print(f"❌ Nilai tidak valid dari {topic}: {value}")
            return

        now = datetime.now()

        # Simpan jika nilai sensor berubah
        if sensor_last_value[label] != value_float:
            sensor_last_change[label] = now
            sensor_last_value[label] = value_float

        latest_sensor_data[label] = value_float
        sensor_last_seen[label] = now

        # Kirim update ke client via WebSocket
        socketio.emit("sensor_update", latest_sensor_data)

        # Simpan ke database jika status kebakaran == 1, jeda minimal 3 menit
        if label == "STATUS_KEBAKARAN" and value_float == 1.0:
            if last_fire_status_logged is None or (now - last_fire_status_logged).total_seconds() >= FIRE_LOG_COOLDOWN_SECONDS:
                last_fire_status_logged = now

                # Kirim notifikasi
                try:
                    from app.src.services.notification_service import notify_sensor_data_Service
                    notify_sensor_data_Service(
                        f"🚨 Peringatan! Lakukan pengecekan kebakaran di ruang penyimpanan bahan bakar. Dashboard: {FLASK_URL}",
                        app_context_data
                    )
                except Exception as e:
                    print(f"❌ Gagal mengirim notifikasi: {e}")

                # Simpan ke database
                try:
                    with app_context_data:
                        create_data_sensor_repository({
                            "api": latest_sensor_data["API"],
                            "asap": latest_sensor_data["ASAP"],
                            "suhu": latest_sensor_data["SUHU"],
                            "kebakaran": 1,
                            "dibuat_sejak": now.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    print(f"🔥 Status kebakaran disimpan di DB pada {now}")
                except Exception as e:
                    print(f"❌ Gagal menyimpan data status kebakaran: {e}")
            else:
                print("⏳ Status kebakaran terdeteksi, tapi masih dalam cooldown logging.")

    return handle_sensor_data


# CEK SENSOR STALE
def check_sensor_status():
    now = datetime.now()
    updated = False

    for label, last_seen in sensor_last_seen.items():
        last_change = sensor_last_change.get(label)
        val = latest_sensor_data[label]

        # Reset data jika tidak berubah selama 24 jam
        if last_change and (now - last_change).total_seconds() > SENSOR_RESET_HOURS * 3600:
            if val is not None:
                latest_sensor_data[label] = None
                updated = True
                print(f"⚠️ Data {label} tidak berubah 24 jam, direset.")

        # Kirim peringatan jika 1 menit tidak berubah
        if last_seen and (now - last_seen).total_seconds() > SENSOR_STALE_SECONDS:
            if not sensor_alert_sent[label]:
                notify_sensor_data_Service(
                    f"🚨 Peringatan: Sensor {label} tidak berubah lebih dari 1 menit."
                    f"Cek sinyal/perangkat.\nDashboard: {FLASK_URL}",
                    app_context
                )
                sensor_alert_sent[label] = True
                print(f"🚨 WARNING: {label} stagnan >1 menit")

    if updated:
        socketio.emit("sensor_update", latest_sensor_data)

# Inisialisasi waktu cek rutin
def init_next_check_times():
    now = datetime.now()
    next_times = {}
    for jam in check_times:
        t = now.replace(hour=jam % 24, minute=0, second=0, microsecond=0)
        if t <= now:
            t += timedelta(days=1)
        next_times[jam] = t
    return next_times

next_check_time = init_next_check_times()

# Jalankan MQTT
def run_mqtt_service(app_instance):
    global client, app_context
    app_context = app_instance

    print(f"🔌 Menghubungkan ke MQTT {BROKER}:{PORT}")
    client = paho.Client(client_id="iot_fire_monitor", protocol=paho.MQTTv5)
    client.username_pw_set(USERNAME, PASSWORD)
    client.tls_set(ca_certs=certifi.where(), tls_version=ssl.PROTOCOL_TLS_CLIENT)

    client.on_connect = on_connect
    for topic, _ in TOPICS:
        client.message_callback_add(topic, handle_sensor_data_factory(app_context))

    try:
        client.connect(BROKER, PORT)
        client.loop_start()
    except Exception as e:
        print(f"❌ Gagal koneksi: {e}")
        socketio.emit("mqtt_error", {"error": str(e)})
        return

    try:
        while True:
            now = datetime.now()
            for jam in check_times:
                if now >= next_check_time[jam]:
                    print(f"⏱️ Cek status sensor jam {jam}")
                    check_sensor_status()
                    next_check_time[jam] += timedelta(days=1)
            time.sleep(60)

    except KeyboardInterrupt:
        print("🛑 MQTT dimatikan")
        client.disconnect()
        client.loop_stop()
