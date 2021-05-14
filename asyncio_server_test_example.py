#!/usr/bin/env python3
"""
Pymodbus Asyncio Server Example
--------------------------------------------------------------------------
The asyncio server is implemented in pure python without any third
party libraries (unless you need to use the serial protocols which require
asyncio-pyserial). This is helpful in constrained or old environments where using
twisted is just not feasible.
--------------------------------------------------------------------------
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


# --------------------------------------------------------------------------- #
# configure the service logging
# --------------------------------------------------------------------------- #
import logging
FORMAT = ('%(asctime)-15s %(threadName)-15s'
          ' %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# ----------------------------------------------------------------------- #
# Data references for modbus
# ----------------------------------------------------------------------- #
di = 2
di_addr = 1
co = 5
co_addr = 1
hr = 3
hr_addr = 1
ir = 4
ir_addr = 1

# ----------------------------------------------------------------------- #
# initialize your data store with fake data
# ----------------------------------------------------------------------- #
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(di_addr, [True, False]*32),
    co=ModbusSequentialDataBlock(co_addr, [True]*64),
    hr=ModbusSequentialDataBlock(hr_addr, [17]*32),
    ir=ModbusSequentialDataBlock(ir_addr, [18]*32))
context = ModbusServerContext(slaves=store, single=True)
# This loads each of the four main data types with the data specified
# In this case, Digital input will get loaded with 64 bits total of [1,0...]
# Coils will all be true (64 total)
# All 32, 16-bit, holding registers will be 17
# and all 32, 16-bit, input registers will be 18
# All datasets start at address 1, as address 0 is invalid in Modbus
# Though all data points have the same address, they are stored and addressed separatly


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
    
    await StartTcpServer(context, identity=identity, address=("192.168.3.123", 
                         5020), allow_reuse_address=True, defer_start=False)
    

async def update_modbus_data(context):
    while 1: #required for asyncio looping. if the process exits it never calls again
        """ A worker process that runs every so often and
        updates live values of the context. It should be noted
        that there is a race condition for the update.
        """
        slave_id = 0x00
        
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

        context[slave_id].setValues(di, di_addr-1, digital_inputs)
        #above updates the DI values in the modbus system
        
        await asyncio.sleep(5) # arbitrary sleep in seconds based on desired update rate
    
async def runrunrun():
    await asyncio.gather(
        run_server(),
        update_modbus_data(context),
        )
    return 0

if __name__ == "__main__":
    asyncio.run(runrunrun())
