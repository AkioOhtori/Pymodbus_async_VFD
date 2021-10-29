#!/usr/bin/env python3
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from time import sleep
import time
import sys
import random
import logging
FORMAT = ('%(asctime)-12s'
          ' %(levelname)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# User Inputs
start = input("Enter start address: (ex: 192.168.1.1) ")
finish = input("Enter stop address: (ex: 192.168.1.254) ")
sts = input("Enter sleep time in seconds between attempts (default = 0.2s) ")
print("What do you want the log name to be? (default: log.txt)")
file = input("WARNING: THIS WILL OVERWRITE EXISTING FILES! ")

# Defaults
if start == "": start = "192.168.3.45"
if finish == "": finish = "192.168.3.55"
if file == "": file = "log.txt"
if sts == "": sts = "0.2"
f = open(file, "wt")
f.write("Starting Modbus Scan at " + str(time.asctime()) + " of range " + \
start + " to " + finish + "\n")
f.close()

s = []
e = []

# Split inputs into digestible chunks
s = (start.split("."))
e = (finish.split("."))

# Check IP length (x.x.x.x)
if len(s) != 4:
	print("ERROR: Invalid Start Address")
	exit()
if len(e) == 1:
	a = ["10","10","10",e[0]]
	e = a
	print(e)
	
if len(e) != 4:
	print("ERROR: Invalid End Address")
	exit()

# Check IP range is within bounds
try:
	for x in range(len(s)):
		if int(s[x]) < 0 or int(s[x]) > 255 \
		or int(e[x]) < 0 or int(e[x]) > 255:
			print("IP Address out of range!")
			exit()
except:
	print("Unable to parse IP address!")
	exit()

# Check range is sequential
if int(s[3]) > int(e[3]):
	print("ERROR: To Infinity and Beyond!")
	exit()

# Validate Sleep
try: st = float(sts)
except:
	print("ERROR: Time is not a number!")
	exit()

# Check to see if the range is larger than a /16
if ((s[2] != e[2]) or (s[1] != e[1]) or (s[0] != e[0])):
        print("\nThis tool only works with /16s at this time.")
        print("Will scan the range " + s[0] + "." + s[1] + "." + s[2] + ".0\n")
        print("Starting in 5 seconds!\n")
        sleep(5)

# Make the tempate for the address string
address = str(s[0]+"."+s[1]+"."+s[2]+".")
# Randomize the IP Range Provided by the user
oct = list(range(int(s[3]),int(e[3])+1))
random.shuffle(oct)

for x in range(len(oct)):
	ip = address+str(oct[x])
	RemoteServer = ModbusClient(ip)     #IP address of MODBUS Server (confusing)

	if (RemoteServer.connect()): 
		logging.info("Hit on " +ip)
		open(file, "a").write(time.asctime() + " Response from " + ip + "!\n")
	RemoteServer.close()
	sleep(st)
print("Done!")
