from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from mqtt import *
from event_manager import *
from aiot_lcd1602 import LCD1602
from machine import Pin, SoftI2C
import time
from aiot_dht20 import DHT20

event_manager.reset()

# Mô tả hàm này...
def MOTION():
  global flag, motion, aiot_lcd1602, aiot_dht20
  if pin1.read_digital()==1:
    if motion == 0:
      mqtt.publish('V3', '1')
      motion = 1
  else:
    motion = 0

aiot_lcd1602 = LCD1602()

aiot_dht20 = DHT20()

# Mô tả hàm này...
def openLCD():
  global flag, motion, aiot_lcd1602, aiot_dht20
  aiot_lcd1602.clear()
  aiot_lcd1602.move_to(0, 0)
  aiot_lcd1602.putstr(('Light: ' + str(str(round(translate((pin0.read_analog()), 0, 4095, 0, 100))) + '%')))
  aiot_lcd1602.move_to(0, 1)
  aiot_lcd1602.putstr(('Temp : ' + str(str(aiot_dht20.dht20_temperature()) + '*C')))

def on_event_timer_callback_I_V_z_j_l():
  global flag, motion
  flag = 1
  mqtt.publish('V1', (round(translate((pin0.read_analog()), 0, 4095, 0, 100))))
  mqtt.publish('V2', (aiot_dht20.dht20_temperature()))

event_manager.add_timer_event(2000, on_event_timer_callback_I_V_z_j_l)

# --- MQTT Callbacks cho Điều khiển (M3) ---
def on_mqtt_message_receive_callback_V4(msg):
  global fan_manual
  if msg == '1':
    fan_manual = 1
  else:
    fan_manual = 0

def on_mqtt_message_receive_callback_V5(msg):
  global light_manual
  if msg == '1':
    light_manual = 1
  else:
    light_manual = 0

def on_mqtt_message_receive_callback_V6(msg):
  global mode
  if msg == '1':
    mode = 1
  else:
    mode = 0

def on_mqtt_message_receive_callback_V7(msg):
  global servo_unlocked, unlock_time
  if msg == '1' or msg == 'unlock':
    pin16.servo_write(90)
    servo_unlocked = 1
    unlock_time = time.ticks_ms()
  elif msg == '0' or msg == 'lock':
    pin16.servo_write(0)
    servo_unlocked = 0

# Mô tả hàm này...
def controlFan():
  global flag, motion, aiot_lcd1602, aiot_dht20, mode, fan_manual
  if mode == 0:
    if (aiot_dht20.dht20_temperature()) > 35:
      pin10.write_analog(round(translate(70, 0, 100, 0, 1023)))
    else:
      pin10.write_analog(round(translate(0, 0, 100, 0, 1023)))
  else:
    if fan_manual == 1:
      pin10.write_analog(round(translate(70, 0, 100, 0, 1023)))
    else:
      pin10.write_analog(round(translate(0, 0, 100, 0, 1023)))

# Mô tả hàm này...
def controlLight():
  global flag, motion, aiot_lcd1602, aiot_dht20, mode, light_manual
  if mode == 0:
    if (round(translate((pin0.read_analog()), 0, 4095, 0, 100))) < 20:
      pin14.write_digital(1)
    else:
      pin14.write_digital(0)
  else:
    pin14.write_digital(light_manual)

# Khóa cửa thông minh (Servo SG90 tại chân P16)
def controlServo():
  pass

if True:
  display.scroll('DEMO')
  mqtt.connect_wifi('Wendy', 'heo260817112005@')
  mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='demo', password='8888')
  mqtt.on_receive_message('V4', on_mqtt_message_receive_callback_V4)
  mqtt.on_receive_message('V5', on_mqtt_message_receive_callback_V5)
  mqtt.on_receive_message('V6', on_mqtt_message_receive_callback_V6)
  mqtt.on_receive_message('V7', on_mqtt_message_receive_callback_V7)
  flag = 0
  motion = 0
  mode = 0
  fan_manual = 0
  light_manual = 0
  servo_unlocked = 0
  unlock_time = 0
  pin16.servo_write(0)

while True:
  event_manager.run()
  mqtt.check_message()
  if flag == 1:
    openLCD()
    flag = 0
  controlFan()
  MOTION()
  controlLight()
  controlServo()
  time.sleep_ms(10)
