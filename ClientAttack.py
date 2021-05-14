#!/usr/bin/env python3
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

RemoteServer = ModbusClient("192.168.3.53")     #IP address of MODBUS Server (confusing, I know)
RemoteServer.connect()          # Connect to modbus server

# Read Test!
coils = RemoteServer.read_coils(16, 6, unit=1)   # Read staus of 8 coils starting at address 0
print("The remote coil 1-8 status is " + str(coils.bits)) #The ".bits" is a list of values from the read
print("The status of remote coil 2 is " + str(coils.bits[1]))

# Now lets write to coil #2 (currently off) and see what happens
x = 10000
while x > 0:
    RemoteServer.write_coils(17,1, unit=1)  #NOTE: reg -1 because 0 reference
    x += -1

coils = RemoteServer.read_coils(16, 6, unit=1)   # Read staus of 8 coils starting at address 0

print("The new remote coil 1-8 status is " + str(coils.bits)) #The ".bits" is a list of values from the read
print("The new status of remote coil 2 is " + str(coils.bits[1]))

RemoteServer.close()  #Don't forget to cleanly exit
