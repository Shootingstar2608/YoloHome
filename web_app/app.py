import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
import time

app = Flask(__name__)
# Enable CORS for SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# MQTT Broker Settings for OhStem
MQTT_BROKER = "mqtt.ohstem.vn"
MQTT_PORT = 1883
MQTT_USERNAME = "demo"
MQTT_PASSWORD = "8888"

# Topics format: <username>/feeds/<topic_name>
MQTT_TOPIC_V1 = "demo/feeds/V1"  # Do am / Anh sang
MQTT_TOPIC_V2 = "demo/feeds/V2"  # Nhiet do
MQTT_TOPIC_V3 = "demo/feeds/V3"  # Chuyen dong

# Store the latest data
latest_data = {
    "V1": 0,
    "V2": 0
}

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(" Thành công kết nối với MQTT Broker!")
        client.subscribe(MQTT_TOPIC_V1)
        client.subscribe(MQTT_TOPIC_V2)
        client.subscribe(MQTT_TOPIC_V3)
        print(f" Đã đăng ký (subscribe) các kênh: {MQTT_TOPIC_V1}, {MQTT_TOPIC_V2}, {MQTT_TOPIC_V3}")
    else:
        print(f" Kết nối thất bại, mã lỗi: {rc}")

def on_message(client, userdata, msg):
    payload = msg.payload.decode("utf-8")
    topic = msg.topic
    print(f" Message received - Topic: {topic} | Message: {payload}")
    
    # Store and broadcast the data via WebSocket
    if topic == MQTT_TOPIC_V1:
        latest_data["V1"] = payload
        socketio.emit('sensor_update', {'topic': 'V1', 'value': payload})
    elif topic == MQTT_TOPIC_V2:
        latest_data["V2"] = payload
        socketio.emit('sensor_update', {'topic': 'V2', 'value': payload})
    elif topic == MQTT_TOPIC_V3:
        if payload == "1":
            socketio.emit('motion_detected', {'status': 'motion'})

# Setup MQTT Client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

def start_mqtt():
    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
        mqtt_client.loop_start()  # Run MQTT loop in background
    except Exception as e:
        print(f"Lỗi khởi tạo MQTT: {e}")

# --- Flask Routes ---
@app.route('/')
def index():
    return render_template('index.html', initial_data=latest_data)

@app.route('/update', methods=['POST'])
def handle_data():
    from flask import request, jsonify
    if request.is_json:
        data = request.get_json()
        temp = data.get("temp")
        humi = data.get("humi")
        light = data.get("light")
        
        # Cập nhật và phát qua WebSockets
        if temp is not None:
            latest_data["V2"] = temp
            socketio.emit('sensor_update', {'topic': 'V2', 'value': temp})
        if humi is not None:
            latest_data["V1"] = humi
            socketio.emit('sensor_update', {'topic': 'V1', 'value': humi})
            
        print(f"--- Nhận dữ liệu HTTP từ Yolobit: {data} ---")
        return jsonify({"status": "Success"}), 200
    return jsonify({"status": "Invalid JSON"}), 400

@socketio.on('connect')
def handle_connect():
    print(" Thiết bị Web đã kết nối (WebSocket).")
    # Gửi ngay dữ liệu hiện tại khi web tải xong
    socketio.emit('sensor_update', {'topic': 'V1', 'value': latest_data["V1"]})
    socketio.emit('sensor_update', {'topic': 'V2', 'value': latest_data["V2"]})

if __name__ == '__main__':
    print("Khởi động server...")
    start_mqtt()
    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
