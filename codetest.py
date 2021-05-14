import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM

PWM_pin = "P9_14"
mtr_forward  = "P9_27"
mtr_reverse = "P9_25"
GPIO.setup(PWM_pin, GPIO.OUT)
GPIO.setup(mtr_forward, GPIO.OUT)
GPIO.setup(mtr_reverse, GPIO.OUT)

while 1:
    speed = 50
    
    GPIO.output(mtr_forward, 1)
    GPIO.output(mtr_reverse, 0)
    PWM.start(PWM_pin, 1)
    PWM.set_duty_cycle(PWM_pin, speed)
    # print("VFD in Run mode " + str(speed))