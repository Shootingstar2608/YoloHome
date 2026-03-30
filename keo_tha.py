from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from mqtt import *
from event_manager import *
from aiot_lcd1602 import LCD1602
from machine import Pin, SoftI2C
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

# Mô tả hàm này...
def controlFan():
  global flag, motion, aiot_lcd1602, aiot_dht20
  if (aiot_dht20.dht20_temperature()) > 31:
    pin10.write_analog(round(translate(70, 0, 100, 0, 1023)))
  else:
    pin10.write_analog(round(translate(0, 0, 100, 0, 1023)))

# Mô tả hàm này...
def controlLight():
  global flag, motion, aiot_lcd1602, aiot_dht20
  if (round(translate((pin0.read_analog()), 0, 4095, 0, 100))) < 20:
    pin14.write_digital(1)
  else:
    pin14.write_digital(0)

if True:
  display.scroll('DEMO')
  mqtt.connect_wifi('Wendy', 'heo260817112005@')
  mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='demo', password='8888')
  flag = 0
  motion = 0

while True:
  event_manager.run()
  mqtt.check_message()
  if flag == 1:
    openLCD()
    flag = 0
  controlFan()
  MOTION()
  controlLight()
  time.sleep_ms(10)
