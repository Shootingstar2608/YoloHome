import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, Response
from flask_socketio import SocketIO
import paho.mqtt.client as mqtt
import json
import threading
import time
import sys
import os

# Đảm bảo có thể import module từ thư mục gốc của project
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from face_service.service import FaceScanner
from ml.infer import OccupancyPredictor

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
MQTT_TOPIC_V4 = "demo/feeds/V4"  # Quạt (Fan)
MQTT_TOPIC_V5 = "demo/feeds/V5"  # Đèn (Light)
MQTT_TOPIC_V6 = "demo/feeds/V6"  # Chế độ Mode (0: Auto, 1: Manual)
MQTT_TOPIC_V7 = "demo/feeds/V7"  # Khóa cửa thông minh (Servo SG90)

# Store the latest data
latest_data = {
    "V1": 0,
    "V2": 0,
    "V4": "0",
    "V5": "0",
    "V6": "0",
    "V7": "0"
}

HISTORY_FILE_PATH = os.path.join(parent_dir, "web_app", "device_history.jsonl")
HISTORY_LOCK = threading.Lock()
HISTORY_DEFAULT_LIMIT = 50


def _history_label(topic, value, source):
    if topic == "V1":
        return f"Ánh sáng: {value}%"
    if topic == "V2":
        return f"Nhiệt độ: {value}°C"
    if topic == "V3" and str(value) == "1":
        return "Cảm biến chuyển động: phát hiện người"
    if topic == "V4":
        return f"Quạt: {'Bật' if str(value) == '1' else 'Tắt'}"
    if topic == "V5":
        return f"Đèn: {'Bật' if str(value) == '1' else 'Tắt'}"
    if topic == "V6":
        return f"Chế độ: {'Manual' if str(value) == '1' else 'Auto'}"
    if topic == "V7":
        is_unlocked = str(value) in ["1", "unlock"]
        if source == "face":
            return f"Khóa cửa: {'Mở khóa bằng AI' if is_unlocked else 'Đóng khóa bằng AI'}"
        return f"Khóa cửa: {'Mở khóa' if is_unlocked else 'Đóng khóa'}"
    return f"{topic}: {value}"


def record_history(topic, value, event_type="device", source="mqtt", message=None):
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "topic": topic,
        "value": value,
        "type": event_type,
        "source": source,
        "message": message if message else _history_label(topic, value, source),
    }

    os.makedirs(os.path.dirname(HISTORY_FILE_PATH), exist_ok=True)
    with HISTORY_LOCK:
        with open(HISTORY_FILE_PATH, "a", encoding="utf-8") as history_file:
            history_file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    socketio.emit("history_event", entry)


def read_recent_history(limit=HISTORY_DEFAULT_LIMIT):
    if not os.path.exists(HISTORY_FILE_PATH):
        return []

    entries = []
    with HISTORY_LOCK:
        with open(HISTORY_FILE_PATH, "r", encoding="utf-8") as history_file:
            for line in history_file:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if limit is None or limit <= 0:
        return entries
    return entries[-limit:]

# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(" Thành công kết nối với MQTT Broker!")
        client.subscribe(MQTT_TOPIC_V1)
        client.subscribe(MQTT_TOPIC_V2)
        client.subscribe(MQTT_TOPIC_V3)
        client.subscribe(MQTT_TOPIC_V4)
        client.subscribe(MQTT_TOPIC_V5)
        client.subscribe(MQTT_TOPIC_V6)
        client.subscribe(MQTT_TOPIC_V7)
        print(f" Đã đăng ký (subscribe) các kênh: V1, V2, V3, V4, V5, V6, V7")
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
        record_history('V1', payload, event_type='sensor', source='mqtt')
        try:
            predict_and_emit(pir_event=0)
        except Exception:
            pass
    elif topic == MQTT_TOPIC_V2:
        latest_data["V2"] = payload
        socketio.emit('sensor_update', {'topic': 'V2', 'value': payload})
        record_history('V2', payload, event_type='sensor', source='mqtt')
        try:
            predict_and_emit(pir_event=0)
        except Exception:
            pass
    elif topic == MQTT_TOPIC_V3:
        if payload == "1":
            socketio.emit('motion_detected', {'status': 'motion'})
            # Tự động kích hoạt luồng quét khuôn mặt khi có chuyển động
            if face_scanner:
                face_scanner.trigger_scan()
            record_history('V3', payload, event_type='sensor', source='mqtt')
            try:
                predict_and_emit(pir_event=1)
            except Exception:
                pass
    elif topic in [MQTT_TOPIC_V4, MQTT_TOPIC_V5, MQTT_TOPIC_V6, MQTT_TOPIC_V7]:
        feed_id = topic.split("/")[-1]
        latest_data[feed_id] = payload
        socketio.emit('device_update', {'topic': feed_id, 'value': payload})
        if feed_id in ["V4", "V5", "V6"]:
            record_history(feed_id, payload, event_type='device', source='mqtt')

# Setup MQTT Client
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Khởi tạo dịch vụ FaceScanner với đường dẫn lưu trữ khuôn mặt
KNOWN_FACES_DIR = os.path.join(parent_dir, "face_service", "known_faces")
face_scanner = FaceScanner(KNOWN_FACES_DIR, mqtt_client, MQTT_TOPIC_V7, socketio)

# Load occupancy predictor (best-effort; model may not exist)
predictor = OccupancyPredictor(os.path.join(parent_dir, 'web_app', 'models', 'occupancy_model.joblib'))

def predict_and_emit(pir_event=0):
    try:
        import datetime
        hour = datetime.datetime.now().hour
        light = latest_data.get('V1', 0)
        temp = latest_data.get('V2', 0)
        face_flag = 1 if str(latest_data.get('V7', '0')) not in ['0', ''] else 0
        pir_count = 1 if pir_event == 1 else 0
        res = predictor.predict(hour, light, temp, pir_count, face_flag)
        socketio.emit('occupancy_update', res)
    except Exception as e:
        print('[occupancy] predict error', e)

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

@app.route('/video_feed')
def video_feed():
    """Stream MJPEG hình ảnh trực tiếp từ Camera nhận diện khuôn mặt"""
    return Response(face_scanner.generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/update', methods=['POST'])
def handle_data():
    if request.is_json:
        data = request.get_json()
        temp = data.get("temp")
        humi = data.get("humi")
        light = data.get("light")
        
        # Cập nhật và phát qua WebSockets
        if temp is not None:
            latest_data["V2"] = temp
            socketio.emit('sensor_update', {'topic': 'V2', 'value': temp})
            record_history('V2', temp, event_type='sensor', source='http')
            try:
                predict_and_emit(pir_event=0)
            except Exception:
                pass
        if humi is not None:
            latest_data["V1"] = humi
            socketio.emit('sensor_update', {'topic': 'V1', 'value': humi})
            record_history('V1', humi, event_type='sensor', source='http')
            try:
                predict_and_emit(pir_event=0)
            except Exception:
                pass
            
        print(f"--- Nhận dữ liệu HTTP từ Yolobit: {data} ---")
        return jsonify({"status": "Success"}), 200
    return jsonify({"status": "Invalid JSON"}), 400


@app.route('/api/history')
def get_history():
    limit = request.args.get('limit', default=HISTORY_DEFAULT_LIMIT, type=int)
    return jsonify({"items": read_recent_history(limit)})

@socketio.on('connect')
def handle_connect():
    print(" Thiết bị Web đã kết nối (WebSocket).")
    # Gửi ngay dữ liệu hiện tại khi web tải xong
    socketio.emit('sensor_update', {'topic': 'V1', 'value': latest_data["V1"]})
    socketio.emit('sensor_update', {'topic': 'V2', 'value': latest_data["V2"]})
    socketio.emit('device_update', {'topic': 'V4', 'value': latest_data["V4"]})
    socketio.emit('device_update', {'topic': 'V5', 'value': latest_data["V5"]})
    socketio.emit('device_update', {'topic': 'V6', 'value': latest_data["V6"]})
    socketio.emit('device_update', {'topic': 'V7', 'value': latest_data["V7"]})

@socketio.on('set_device')
def handle_set_device(data):
    topic = data.get('topic')  # vd: 'V4'
    value = str(data.get('value'))  # vd: '0' hoặc '1'
    if topic in ['V4', 'V5', 'V6', 'V7']:
        full_topic = f"{MQTT_USERNAME}/feeds/{topic}"
        mqtt_client.publish(full_topic, value)
        latest_data[topic] = value
        socketio.emit('device_update', {'topic': topic, 'value': value})
        print(f" Đã gửi lệnh MQTT: {full_topic} -> {value}")


@socketio.on('history_note')
def handle_history_note(data):
    topic = data.get('topic', 'V7')
    value = data.get('value', '1')
    event_type = data.get('type', 'security')
    source = data.get('source', 'web')
    message = data.get('message')
    record_history(topic, value, event_type=event_type, source=source, message=message)

if __name__ == '__main__':
    print("Khởi động server...")
    start_mqtt()
    # Run the Flask app with SocketIO
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
