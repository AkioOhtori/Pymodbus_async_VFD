#!/usr/bin/env python3
"""
Pymodbus Asyncio Server Example
--------------------------------------------------------------------------

The asyncio server is implemented in pure python without any third
party libraries (unless you need to use the serial protocols which require
asyncio-pyserial). This is helpful in constrained or old environments where using
twisted is just not feasible. What follows is an example of its use:
"""
# --------------------------------------------------------------------------- #
# import the various server implementations
# --------------------------------------------------------------------------- #
import asyncio
from pymodbus.version import version
from pymodbus.server.async_io import StartTcpServer

from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.PWM as PWM

# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
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

# ----------------------------------------------------------------------- #
# initialize your data store
# ----------------------------------------------------------------------- #
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(di_addr, [True, False]*32),
    co=ModbusSequentialDataBlock(co_addr, [True]*64),
    hr=ModbusSequentialDataBlock(hr_addr, [17]*32),
    ir=ModbusSequentialDataBlock(ir_addr, [18]*32))
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


async def run_server():

    
    # ----------------------------------------------------------------------- #
    # run the server
    # ----------------------------------------------------------------------- #
    
    await StartTcpServer(context, identity=identity, address=("192.168.3.123", 
                         502), allow_reuse_address=True, defer_start=False)
    

async def update_modbus_data(context):
    while 1: #required for asyncio looping. if the process exits it never calls again
        """ A worker process that runs every so often and
        updates live values of the context. It should be noted
        that there is a race condition for the update.
        """
        slave_id = 0x00
        if 0:
            #read current values, partial reads can also be coded as needed
            digital_inputs = context[slave_id].getValues(di, di_addr-1, count=64)
            coils = context[slave_id].getValues(co, co_addr-1, count=64)
            holding_registers = context[slave_id].getValues(hr, hr_addr-1, count=32)
            input_registers = context[slave_id].getValues(ir, ir_addr-1, count=32)
            
            log.info("The first 8 DIs are: " + str(digital_inputs[0:7]))
            # print(coils)
            # print(holding_registers)
            # print(input_registers)
            digital_inputs[0] = not digital_inputs[0]
            log.info("The first 8 DIs are now: " + str(digital_inputs[0:7])) #Confrm Change
            
            #Hard Coded Safety/ Sanity Checks!
            if holding_registers[HR_SETPOINT] < 0: holding_registers[HR_SETPOINT] = 0
            elif holding_registers[HR_SETPOINT] > 100: holding_registers[HR_SETPOINT] = 100
            
            #Call Motor Routine!
            # MotorControl(holding_registers[HR_SETPOINT]) #await?
            #TODO - Motor reversing safety!
            #TODO - Speed setpoint ramp up/down!
            
            # log.debug("new values: " + str(values))
            context[slave_id].setValues(di, di_addr-1, digital_inputs)
        await asyncio.sleep(5)
    
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
    

async def poop():
    print("Poop")
    while True: 
        # log.debug("updating the context")
        # context = a[0]
        # register = 3
        # slave_id = 0x00
        # address = 0x100
        # values = context[slave_id].getValues(register, address, count=5)
        # values = [v + 1 for v in values]
        # log.debug("new values: " + str(values))
        # context[slave_id].setValues(register, address, values)
        await asyncio.sleep(1)
        print("Pooping")
    # a.stop()
    
    
async def runrunrun():
    await asyncio.gather(
        run_server(),
        update_modbus_data(context),
        )
    return 0

if __name__ == "__main__":
    asyncio.run(runrunrun())
