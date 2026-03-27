from yolobit import *
button_a.on_pressed = None
button_b.on_pressed = None
button_a.on_pressed_ab = button_b.on_pressed_ab = -1
from mqtt import *
from event_manager import *
from machine import Pin, SoftI2C
from aiot_dht20 import DHT20
from aiot_lcd1602 import LCD1602
import time

event_manager.reset()

aiot_dht20 = DHT20()

aiot_lcd1602 = LCD1602()

def on_event_timer_callback_p_n_B_k_S():

  mqtt.publish('V1', (round(translate((pin0.read_analog()), 0, 4095, 0, 100))))
  mqtt.publish('V2', (aiot_dht20.dht20_temperature()))
  aiot_lcd1602.clear()
  aiot_lcd1602.move_to(0, 0)
  aiot_lcd1602.putstr((str(round(translate((pin0.read_analog()), 0, 4095, 0, 100))) + '%'))
  if 0 == 0:
    pass
  aiot_lcd1602.move_to(4, 0)
  aiot_lcd1602.putstr((str(aiot_dht20.dht20_temperature()) + '*C'))
  if pin1.read_digital()==1:
    aiot_lcd1602.move_to(0, 1)
    aiot_lcd1602.putstr('CHAO MUNG')
  if (round(translate((pin0.read_analog()), 0, 4095, 0, 100))) < 36:
    pin3.write_digital(1)
  else:
    pin3.write_digital(0)
  if (aiot_dht20.dht20_temperature()) > 28:
    pin10.write_analog(round(translate(70, 0, 100, 0, 1023)))
  else:
    pin10.write_analog(round(translate(0, 0, 100, 0, 1023)))

event_manager.add_timer_event(2000, on_event_timer_callback_p_n_B_k_S)

if True:
  display.scroll('DEMO')
  mqtt.connect_wifi('Wendy', 'heo260817112005@')
  mqtt.connect_broker(server='mqtt.ohstem.vn', port=1883, username='demo', password='8888')
  display.scroll('OK')

while True:
  mqtt.check_message()
  event_manager.run()
  time.sleep_ms(10)


time.sleep_ms(4000)
