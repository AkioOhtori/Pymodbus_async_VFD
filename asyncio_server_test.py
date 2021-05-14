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
log.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Setup BBB IO
# --------------------------------------------------------------------------- #
PWM_pin = "P9_14"
mtr_forward  = "P9_27"
mtr_reverse = "P9_25"
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
HR_SETPOINT = 0 #speed setpoint
HR_MODE = 1     #operating mode

# Coils
CO_CONNECTED = 0
CO_RUN = 1
CO_FORWARD = 2
CO_REVERSE = 3
CO_BRAKE = 4
CO_ESTOP = 5

# Discrete Inputs
DI_OK = 0
DI_RUNNING = 1
DI_STOPPED = 2
DI_INVALID = 3
DI_ACCEL = 4
DI_DECEL = 5


# Input Registers
IR_TARGET_SPEED = 0
IR_STATUS = 1
'''
Discrete Inputs:
1 - OK
2 - Running
3 - Stopped
4 - Invalid Data Recieved
5 - Accelerating
6 - Decerlerating

Input Registers:
1 - Speed (?)
2 - Status Word (?)


'''

# ----------------------------------------------------------------------- #
# initialize your data store
# ----------------------------------------------------------------------- #
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(di_addr, [True] + [False]*61),
    co=ModbusSequentialDataBlock(co_addr, [False]*64),
    hr=ModbusSequentialDataBlock(hr_addr, [0]*32),
    ir=ModbusSequentialDataBlock(ir_addr, [100]+[0]*31) )
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
        
        # coils[CO_CONNECTED] = 0 #reset connected bit
        
        #read current values, partial reads can also be coded as needed
        # Addresses need to be -1 because of weird offby1 errors
        digital_inputs = context[slave_id].getValues(di, di_addr-1, count=64)
        coils = context[slave_id].getValues(co, co_addr-1, count=64)
        holding_registers = context[slave_id].getValues(hr, hr_addr-1, count=32)
        input_registers = context[slave_id].getValues(ir, ir_addr-1, count=32)
        
        if coils[CO_CONNECTED] == False:
            #TODO This doesn't work if we lose connectivity
            log.info("Waiting for PLC Connection")
            await asyncio.sleep(5)
            continue #if the PLC hasn't made contact yet, do not go TODO failsafe

        # log.info("The first 8 DIs are: " + str(digital_inputs[0:7]))
        # print(coils)
        # print(holding_registers)
        # print(input_registers)
        # digital_inputs[0] = not digital_inputs[0]
        
        # log.info("The first 8 DIs are now: " + str(digital_inputs[0:7])) #Confrm Change
        
        #Hard Coded Safety/ Sanity Checks!
        if holding_registers[HR_SETPOINT] < 0: holding_registers[HR_SETPOINT] = 0
        elif holding_registers[HR_SETPOINT] > 100: holding_registers[HR_SETPOINT] = 100
        
        # Ramp Speed
        if coils[CO_RUN] == 0:
            digital_inputs[DI_RUNNING] = False
            input_registers[IR_TARGET_SPEED] = 100
        else:
            digital_inputs[DI_RUNNING] = True
            RAMP = 5
            speed_diff = holding_registers[HR_SETPOINT] - input_registers[IR_TARGET_SPEED]
            # 100 = Stopped, 0 = Full speed; No I don't know why
            if speed_diff > 0: #need to slow down
                digital_inputs[DI_ACCEL] = True
                digital_inputs[DI_DECEL] = False
                if speed_diff > RAMP: input_registers[IR_TARGET_SPEED] += RAMP
                elif speed_diff <= RAMP: input_registers[IR_TARGET_SPEED] = holding_registers[HR_SETPOINT]
            elif speed_diff < 0: #need to speed up
                digital_inputs[DI_DECEL] = True
                digital_inputs[DI_ACCEL] = False
                RAMP = -RAMP
                if speed_diff < RAMP: input_registers[IR_TARGET_SPEED] += RAMP
                elif speed_diff >= RAMP: input_registers[IR_TARGET_SPEED] = holding_registers[HR_SETPOINT]
            else:
                digital_inputs[DI_DECEL] = False
                digital_inputs[DI_ACCEL] = False
                
            if input_registers[IR_TARGET_SPEED] < 0: input_registers[IR_TARGET_SPEED] = 0
            elif input_registers[IR_TARGET_SPEED] > 100: input_registers[IR_TARGET_SPEED] = 100
        # print(input_registers[IR_TARGET_SPEED])
        
        #Call Motor Routine!
        MotorControl(holding_registers[HR_SETPOINT], run=coils[CO_RUN]) #await?
        #TODO - Motor reversing safety!
        
        # log.debug("new values: " + str(values))
        context[slave_id].setValues(di, di_addr-1, digital_inputs)
        context[slave_id].setValues(ir, ir_addr-1, input_registers)
        
        await asyncio.sleep(1)
    
def MotorControl(speed, run=0, forward=1, reverse=0, brake=0):
    # TODO Made do good
    if run == True:
        #make the motor go
        GPIO.output(mtr_forward, forward)
        GPIO.output(mtr_reverse, reverse)
        PWM.start(PWM_pin, 1)
        PWM.set_duty_cycle(PWM_pin, speed)
        log.info("VFD in Run mode " + str(speed))
    elif brake == True:
        GPIO.output(mtr_forward, 0)
        GPIO.output(mtr_reverse, 0)
        log.info("VFD in Brake mode")
    else:
        GPIO.output(mtr_forward, 1)
        GPIO.output(mtr_reverse, 1)
        log.info("VFD in Coast mode")
    
    
async def runrunrun():
    await asyncio.gather(
        run_server(),
        update_modbus_data(context),
        )
    return 0

if __name__ == "__main__":
    asyncio.run(runrunrun())
