# Hướng dẫn kết nối phần cứng YoloHome

Tài liệu này hướng dẫn chi tiết cách cắm các thiết bị ngoại vi vào board mở rộng của YoloBit để hệ thống YoloHome hoạt động chính xác.

## 1. Bảng cấu hình chân cắm

| Thiết bị | Cổng/Chân trên YoloBit | Loại tín hiệu | Chức năng |
| :--- | :--- | :--- | :--- |
| **Cảm biến Ánh sáng** | **P0** | Analog | Đo cường độ ánh sáng môi trường |
| **Cảm biến Chuyển động PIR** | **P1** | Digital | Phát hiện người di chuyển để kích hoạt Camera |
| **Quạt (Động cơ Mini)** | **P10** | Analog/PWM | Điều khiển làm mát (Tự động/Thủ công) |
| **Đèn LED / Rơ-le** | **P14** | Digital | Điều khiển chiếu sáng (Tự động/Thủ công) |
| **Động cơ Servo SG90** | **P16** | Servo/PWM | Khóa/Mở cửa thông minh |
| **Cảm biến DHT20** | **Cổng I2C** | I2C | Đo Nhiệt độ và Độ ẩm |
| **Màn hình LCD1602** | **Cổng I2C** | I2C | Hiển thị thông số hệ thống |

---

## 2. Chi tiết cách cắm từng thiết bị

### 2.1. Cảm biến Ánh sáng (Light Sensor)
- **Vị trí:** Cắm vào cổng **P0**.
- **Cách cắm:** Sử dụng cáp Grove 4 dây. Một đầu cắm vào cảm biến, đầu còn lại cắm vào cổng P0 trên mạch mở rộng.

### 2.2. Cảm biến Chuyển động (PIR Motion Sensor)
- **Vị trí:** Cắm vào cổng **P1**.
- **Cách cắm:** Sử dụng cáp Grove. Cảm biến này sẽ gửi tín hiệu '1' về chân P1 khi có chuyển động, kích hoạt hệ thống nhận diện khuôn mặt trên máy tính.

### 2.3. Quạt Mini (Fan Module)
- **Vị trí:** Cắm vào cổng **P10**.
- **Cách cắm:** Cắm vào cổng P10. Hệ thống sử dụng chân này để điều khiển tốc độ quạt hoặc bật/tắt dựa trên nhiệt độ từ DHT20.

### 2.4. Đèn (LED hoặc Module Relay)
- **Vị trí:** Cắm vào cổng **P14**.
- **Cách cắm:** Cắm vào cổng P14. Đèn sẽ tự động bật khi ánh sáng (P0) yếu hoặc điều khiển qua giao diện web.

### 2.5. Khóa cửa (Servo SG90)
- **Vị trí:** Cắm vào hàng chân **P16**.
- **Cách cắm:** 
    - Dây **Cam** (Tín hiệu): Cắm vào chân **S** (Signal).
    - Dây **Đỏ** (Dương): Cắm vào chân **V** (VCC/5V).
    - Dây **Nâu** (Âm): Cắm vào chân **G** (GND).
- **Lưu ý:** Servo cần nguồn ổn định để hoạt động trơn tru.

### 2.6. Thiết bị I2C (DHT20 & LCD1602)
- **Vị trí:** Cắm vào các cổng có nhãn **I2C** trên mạch mở rộng.
- **Cách cắm:** Board mở rộng YoloBit thường có nhiều cổng I2C. Bạn có thể cắm DHT20 vào một cổng và LCD1602 vào cổng còn lại. Cả hai thiết bị sẽ dùng chung đường bus I2C để giao tiếp.

---

## 3. Kiểm tra sau khi cắm
1. Đảm bảo tất cả các giắc cắm Grove đã được đẩy sát vào cổng.
2. Kiểm tra dây Servo đã đúng thứ tự màu (Cam - Đỏ - Nâu).
3. Cấp nguồn cho YoloBit qua cổng USB hoặc Pin.
4. Quan sát màn hình LCD: Nếu hiển thị thông số Nhiệt độ và Ánh sáng là bạn đã kết nối thành công DHT20 và Light Sensor.
5. Thử đưa tay trước cảm biến PIR: Nếu hệ thống báo có chuyển động trên Web Dashboard là P1 đã hoạt động.
