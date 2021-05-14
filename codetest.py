import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
from time import sleep

PWM_pin = "P9_14"
mtr_forward  = "P9_27"
mtr_reverse = "P9_25"
GPIO.setup(PWM_pin, GPIO.OUT)
GPIO.setup(mtr_forward, GPIO.OUT)
GPIO.setup(mtr_reverse, GPIO.OUT)

GPIO.setup("P9_30", GPIO.OUT)
GPIO.output("P9_30", GPIO.LOW)


speed = 50
GPIO.output(mtr_forward, GPIO.HIGH)
GPIO.output(mtr_reverse, GPIO.LOW)
PWM.start(PWM_pin, 1)
PWM.set_duty_cycle(PWM_pin, speed)
while 1:
    
    

    print("VFD in Run mode " + str(speed))
    sleep(5)
    
print("Hello")