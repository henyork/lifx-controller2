from machine import Pin
import time

print("running button.py")

button_pin_1 = 32

button = Pin(button_pin_1, Pin.IN, Pin.PULL_UP)

while True:
    if button.value() == 0:
        print("button pressed")
        time.sleep(0.2)
    #print(button.value())
    time.sleep(0.05)