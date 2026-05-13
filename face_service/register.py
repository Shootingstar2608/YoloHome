import os
import cv2
import pickle
import argparse
import face_recognition

# Thư mục lưu trữ các khuôn mặt đã đăng ký (dưới dạng vector đặc trưng .pkl)
KNOWN_FACES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "known_faces")

def register_face(name, image_path=None):
    """
    Đăng ký khuôn mặt mới bằng cách trích xuất vector đặc trưng (128-d) 
    từ file ảnh hoặc chụp trực tiếp từ Webcam.
    """
    os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
    
    rgb_image = None

    if image_path:
        if not os.path.exists(image_path):
            print(f"[Lỗi] Không tìm thấy file ảnh tại: {image_path}")
            return
        print(f"[Register] Đang đọc ảnh từ {image_path}...")
        image = face_recognition.load_image_file(image_path)
        rgb_image = image
    else:
        print("[Register] Đang khởi động Webcam...")
        print(">>> HƯỚNG DẪN: Hãy nhìn thẳng vào camera và nhấn phím 's' để CHỤP, hoặc 'q' để THOAT.")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[Lỗi] Không thể kết nối với Webcam. Vui lòng kiểm tra lại thiết bị.")
            return
            
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Lật ảnh giống gương để người dùng dễ nhìn
            display_frame = cv2.flip(frame, 1)
            
            # Hiển thị thông tin hướng dẫn
            cv2.putText(display_frame, "Nhin thang vao camera", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, "Nhan 's' de CHUP", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(display_frame, "Nhan 'q' de THOAT", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow("Smart Door Lock - Register Face", display_frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('s'):
                # Lưu ý: frame gốc chưa flip để trích xuất chính xác
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                break
            elif key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                print("[Register] Đã hủy thao tác đăng ký.")
                return
                
        cap.release()
        cv2.destroyAllWindows()
        
    print("[Register] Đang phân tích và phát hiện khuôn mặt...")
    boxes = face_recognition.face_locations(rgb_image)
    
    if not boxes:
        print("[Lỗi] Không tìm thấy khuôn mặt nào! Vui lòng đảm bảo ánh sáng tốt và không bị che mặt.")
        return
        
    if len(boxes) > 1:
        print(f"[Cảnh báo] Phát hiện {len(boxes)} khuôn mặt trong khung hình. Sẽ trích xuất khuôn mặt rõ nhất.")
        
    encodings = face_recognition.face_encodings(rgb_image, boxes)
    if not encodings:
        print("[Lỗi] Không thể trích xuất đặc trưng khuôn mặt.")
        return
        
    encoding = encodings[0]
    
    # Lưu file pickle
    output_path = os.path.join(KNOWN_FACES_DIR, f"{name}.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(encoding, f)
        
    print(f"[Thành công] Đã đăng ký thành công khuôn mặt cho '{name}'!")
    print(f"📁 Đường dẫn file dữ liệu: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Đăng ký khuôn mặt mới cho hệ thống Smart Door Lock")
    parser.add_argument("--name", required=True, help="Tên người dùng (viết liền không dấu hoặc đặt trong ngoặc kép)")
    parser.add_argument("--image", help="Đường dẫn đến file ảnh (nếu không muốn dùng Webcam)")
    args = parser.parse_args()
    
    register_face(args.name, args.image)
