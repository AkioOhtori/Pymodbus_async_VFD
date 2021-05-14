#!/usr/bin/env python
"""
Pymodbus Server With Updating Thread
--------------------------------------------------------------------------

This is an example of having a background thread updating the
context while the server is operating. This can also be done with
a python thread::

    from threading import Thread

    thread = Thread(target=updating_writer, args=(context,))
    thread.start()
"""
# --------------------------------------------------------------------------- #
# import the modbus libraries we need
# --------------------------------------------------------------------------- #
from pymodbus.version import version
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusAsciiFramer
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM

import time
# --------------------------------------------------------------------------- #
# import the twisted libraries we need
# --------------------------------------------------------------------------- #
from twisted.internet.task import LoopingCall

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


# --------------------------------------------------------------------------- #
# Setup BBB IO
# --------------------------------------------------------------------------- #
PWM_pin = "P9_14"
mtr_forward  = "P8_14"
mtr_reverse = "P9_15"
GPIO.setup(PWM_pin, GPIO.OUT)
GPIO.setup(mtr_forward, GPIO.OUT)
GPIO.setup(mtr_reverse, GPIO.OUT)

di = 2
di_addr = 1
co = 5
co_addr = 1
hr = 3
hr_addr = 1
ir = 4
ir_addr = 1

# --------------------------------------------------------------------------- #
# Modbus Registers
# --------------------------------------------------------------------------- #

# Holding Registers:
HR_SETPOINT = 1
HR_MODE = 2

'''
Discrete Inputs:
1 - OK
2 - Running
3 - Stopped
4 - Invalid Data Recieved
5 - Accelerating
6 - Decerlerating

Coils:
1 - Run
2 - Forward
3 - Backwards
4 - Brake
5 - E-STOP (?)
6 - 

Input Registers:
1 - Speed Setpoint
1 - Speed (?)
2 - Status Word (?)
'''


# --------------------------------------------------------------------------- #
# define your callback process
# --------------------------------------------------------------------------- #


def updating_writer(a):
    """ A worker process that runs every so often and
    updates live values of the context. It should be noted
    that there is a race condition for the update.

    :param arguments: The input arguments to the call
    """
    log.debug("Updating Motor Stuff")
    
    context = a #no idea why this is but lets roll with it
    slave_id = 0x00
    
    #read current values (could skip this for inputs if state is constant)
    digital_inputs = context[slave_id].getValues(di, di_addr, count=8)
    # coils = context[slave_id].getValues(5, co_addr, count=5)
    holding_registers = context[slave_id].getValues(hr, hr_addr, count=8)
    # input_registers = context[slave_id].getValues(4, ir_addr, count=5)
    
    
    print(digital_inputs)
    # print(coils)
    # print(holding_registers)
    # print(input_registers)
    digital_inputs[0] = not digital_inputs[0]
    print(digital_inputs)
    
    #Hard Coded Safety/ Sanity Checks!
    if holding_registers[HR_SETPOINT] < 0: holding_registers[HR_SETPOINT] = 0
    elif holding_registers[HR_SETPOINT] > 100: holding_registers[HR_SETPOINT] = 100
    
    #Call Motor Routine!
    MotorControl(holding_registers[HR_SETPOINT]) #await?
    #TODO - Motor reversing safety!
    #TODO - Speed setpoint ramp up/down!
    
    # log.debug("new values: " + str(values))
    context[slave_id].setValues(di, di_addr, digital_inputs)
    
def MotorControl(speed, run=0, forward=1, reverse=0, brake=0):
    # TODO Made do good
    if run == True:
        #make the motor go
        GPIO.output(mtr_forward, forward)
        GPIO.output(mtr_reverse, reverse)
        PWM.start(PWM_pin, 1)
         #while c[0] == True:????
        PWM.set_duty_cycle(PWM_pin, speed)
        log.debug("VFD in Run mode")
    elif brake == True:
        GPIO.output(mtr_forward, 0)
        GPIO.output(mtr_reverse, 0)
        log.debug("VFD in Brake mode")
    else:
        GPIO.output(mtr_forward, 1)
        GPIO.output(mtr_reverse, 1)
        log.debug("VFD in Coast mode")


def run_updating_server():
    # ----------------------------------------------------------------------- # 
    # initialize your data store
    # ----------------------------------------------------------------------- # 
    
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(di_addr, [True, False]*32),
        co=ModbusSequentialDataBlock(co_addr, [True]*64),
        hr=ModbusSequentialDataBlock(hr_addr, [17]*32),
        ir=ModbusSequentialDataBlock(ir_addr, [18]*32))
        # di=ModbusSequentialDataBlock(0, [True, False]*32),
        # co=ModbusSequentialDataBlock(0, [True, True, False, False]*16),
        # hr=ModbusSequentialDataBlock(0, [17]*32),
        # ir=ModbusSequentialDataBlock(0, [18]*32))
    context = ModbusServerContext(slaves=store, single=True)

    
    # ----------------------------------------------------------------------- # 
    # initialize the server information
    # ----------------------------------------------------------------------- # 
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'BadNet'
    identity.ProductCode = 'FML'
    identity.VendorUrl = 'http://github.com/riptideio/pymodbus/'
    identity.ProductName = 'BadBeagleBone'
    identity.ModelName = 'BadMotorController'
    identity.MajorMinorRevision = version.short()
    
    # ----------------------------------------------------------------------- # 
    # run the server you want
    # ----------------------------------------------------------------------- # 
    time = 5
    loop = LoopingCall(f=updating_writer, a=context)
    loop.start(time, now=False) # initially delay by time
    StartTcpServer(context, identity=identity, address=("192.168.3.123", 5020))


if __name__ == "__main__":
    run_updating_server()
