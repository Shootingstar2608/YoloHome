import os
import cv2
import time
import pickle
import threading
import numpy as np
import face_recognition

class FaceScanner:
    def __init__(self, known_faces_dir, mqtt_client, unlock_topic, socketio):
        self.known_faces_dir = known_faces_dir
        self.mqtt_client = mqtt_client
        self.unlock_topic = unlock_topic
        self.socketio = socketio

        self.is_scanning = False
        self.scan_start_time = 0
        self.scan_duration = 10.0  # Tự động tắt camera sau 10 giây nếu không nhận diện được ai

        self.known_encodings = []
        self.known_names = []
        self.lock = threading.Lock()
        self.load_known_faces()

        # Tạo sẵn ảnh Standby mặc định khi camera không hoạt động
        standby_img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Background tối màu xám xanh sang trọng
        standby_img[:] = (20, 25, 30)
        cv2.putText(standby_img, "CAMERA STANDBY", (180, 220), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (100, 120, 140), 2)
        cv2.putText(standby_img, "Waiting for motion detection (PIR Sensor)...", (120, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (80, 90, 100), 1)
        ret, buffer = cv2.imencode('.jpg', standby_img)
        self.standby_frame = buffer.tobytes()

    def load_known_faces(self):
        """Tải toàn bộ dữ liệu khuôn mặt đã đăng ký từ thư mục known_faces"""
        self.known_encodings = []
        self.known_names = []
        if not os.path.exists(self.known_faces_dir):
            os.makedirs(self.known_faces_dir, exist_ok=True)
            return
            
        for filename in os.listdir(self.known_faces_dir):
            if filename.endswith(".pkl"):
                name = os.path.splitext(filename)[0]
                filepath = os.path.join(self.known_faces_dir, filename)
                try:
                    with open(filepath, "rb") as f:
                        encoding = pickle.load(f)
                        self.known_encodings.append(encoding)
                        self.known_names.append(name)
                except Exception as e:
                    print(f"[FaceService] Lỗi đọc dữ liệu {filename}: {e}")
                    
        print(f"[FaceService] Đã tải {len(self.known_names)} khuôn mặt hợp lệ: {self.known_names}")

    def trigger_scan(self):
        """Được gọi khi cảm biến chuyển động phát hiện có người"""
        with self.lock:
            if self.is_scanning:
                return  # Đang quét rồi thì bỏ qua
            # Tải lại danh sách đề phòng có người mới đăng ký
            self.load_known_faces()
            self.is_scanning = True
            self.has_unlocked = False
            self.scan_start_time = time.time()
            self.stop_scan_time = self.scan_start_time + self.scan_duration
            self.socketio.emit("face_status", {
                "status": "scanning", 
                "message": "Phát hiện chuyển động! Đang khởi động Camera phân tích khuôn mặt..."
            })
            print("[FaceService] 🟡 Kích hoạt Camera quét mặt (Triggered by Motion Sensor)")

    def generate_frames(self):
        """Generator stream hình ảnh MJPEG liên tục cho trình duyệt Web"""
        cap = None
        while True:
            is_active = False
            with self.lock:
                is_active = self.is_scanning
                if not hasattr(self, 'stop_scan_time'):
                    self.stop_scan_time = time.time() + self.scan_duration
                # Kiểm tra quá thời gian quét hoặc hết thời gian duy trì stream
                if is_active and (time.time() > self.stop_scan_time):
                    self.is_scanning = False
                    is_active = False
                    if not getattr(self, 'has_unlocked', False):
                        self.socketio.emit("face_status", {
                            "status": "timeout", 
                            "message": "Hết thời gian quét (10s). Không nhận diện được khuôn mặt hợp lệ."
                        })
                    print("[FaceService] 🔴 Tự động tắt Camera để bảo vệ hệ thống")
                    if cap:
                        cap.release()
                        cap = None

            # Nếu camera không được kích hoạt, stream ảnh Standby
            if not is_active:
                if cap:
                    cap.release()
                    cap = None
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + self.standby_frame + b'\r\n')
                time.sleep(0.5)  # Tiết kiệm băng thông khi standby
                continue

            # --- TRẠNG THÁI CAMERA HOẠT ĐỘNG ---
            if cap is None:
                cap = cv2.VideoCapture(0)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                if not cap.isOpened():
                    print("[FaceService] Lỗi: Không thể mở thiết bị Camera")
                    with self.lock:
                        self.is_scanning = False
                    self.socketio.emit("face_status", {
                        "status": "error", 
                        "message": "Lỗi phần cứng: Không thể kết nối với Camera PC."
                    })
                    continue

            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue

            # Lật ảnh giống gương
            frame = cv2.flip(frame, 1)

            # Thu nhỏ ảnh để tăng tốc độ nhận diện theo thời gian thực
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            boxes = face_recognition.face_locations(rgb_small_frame)
            encodings = face_recognition.face_encodings(rgb_small_frame, boxes)

            face_matched = False
            matched_name = "Unknown"

            for (top, right, bottom, left), face_encoding in zip(boxes, encodings):
                # Phóng to lại tọa độ do đã scale 0.5
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2

                name = "Unknown"
                color = (0, 0, 255)  # Khung màu Đỏ cảnh báo người lạ

                if self.known_encodings:
                    distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                    best_match_index = np.argmin(distances)
                    # Ngưỡng tin cậy nghiêm ngặt (càng nhỏ càng giống)
                    if distances[best_match_index] < 0.45:
                        name = self.known_names[best_match_index]
                        color = (0, 255, 0)  # Khung màu Xanh cho phép mở khóa
                        face_matched = True
                        matched_name = name

                # Vẽ khung nhận diện và nhãn tên trực quan
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 30), (right, bottom), color, cv2.FILLED)
                cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            # Mã hóa sang JPEG streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Xử lý ngay lập tức nếu khớp mặt thành công
            if face_matched:
                with self.lock:
                    self.is_scanning = False
                    
                # Gửi bản tin MQTT kích hoạt bo mạch YoloBit mở khóa Servo
                self.mqtt_client.publish(self.unlock_topic, "unlock")
                
                # Thông báo tới Frontend Web UI
                self.socketio.emit("face_status", {
                    "status": "success",
                    "message": f"Nhận diện thành công! Xin chào {matched_name}. Đã gửi lệnh mở khóa cửa.",
                    "user": matched_name
                })
                
                print(f"[FaceService] 🟢 XÁC THỰC THÀNH CÔNG: '{matched_name}' — Đã phát lệnh mở cửa tới YoloBit")
                
                if cap:
                    cap.release()
                    cap = None
                # Dừng hình 1.5 giây để người dùng kịp nhìn thấy khung viền xanh và tên mình trên web
                time.sleep(1.5)
