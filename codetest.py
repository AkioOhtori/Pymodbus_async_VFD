import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM
from time import sleep

PWM_pin = "P9_14"
mtr_forward  = "P9_27"
mtr_reverse = "P9_30"
GPIO.setup(PWM_pin, GPIO.OUT)
GPIO.setup(mtr_forward, GPIO.OUT, GPIO.PUD_DOWN)
GPIO.setup(mtr_reverse, GPIO.OUT, GPIO.PUD_DOWN)

# GPIO.setup("P9_30", GPIO.OUT, GPIO.PUD_DOWN)
# GPIO.output("P9_30", GPIO.LOW)


speed = 20
GPIO.output(mtr_forward, GPIO.HIGH)
GPIO.output(mtr_reverse, GPIO.LOW)
PWM.start(PWM_pin, 1, 1500)
PWM.set_duty_cycle(PWM_pin, speed)

x = 1
while 1:
    # if x:
    #     GPIO.output(mtr_forward, GPIO.HIGH)
    #     GPIO.output(mtr_reverse, GPIO.LOW)
    #     GPIO.output("P9_30", GPIO.LOW)
    #     x = 0
    # else:
    #     GPIO.output(mtr_forward, GPIO.LOW)
    #     GPIO.output(mtr_reverse, GPIO.HIGH)
    #     GPIO.output("P9_30", GPIO.HIGH)
    #     x = 1   

    print("VFD in Run mode " + str(speed))
    sleep(2)
    
print("Hello")