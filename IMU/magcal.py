'''
    Find Heading by using HMC5883L interface with Raspberry Pi using Python
	http://www.electronicwings.com
'''
import smbus		#import SMBus module of I2C
from time import sleep  #import sleep
import math
import matplotlib.pyplot as plt

#some MPU6050 Registers and their Address
Register_A     = 0              #Address of Configuration register A
Register_B     = 0x01           #Address of configuration register B
Register_mode  = 0x02           #Address of mode register

X_axis_H    = 0x03              #Address of X-axis MSB data register
Z_axis_H    = 0x05              #Address of Z-axis MSB data register
Y_axis_H    = 0x07              #Address of Y-axis MSB data register
declination = -0.00669          #define declination angle of location where measurement going to be done
pi          = 3.14159265359     #define pi value

#Calibration variable
xH_List = []
yH_List = []

xH_cList = []
yH_cList = []

def Magnetometer_Init():
        #write to Configuration Register A
        bus.write_byte_data(Device_Address, Register_A, 0x70)

        #Write to Configuration Register B for gain
        bus.write_byte_data(Device_Address, Register_B, 0xa0)

        #Write to mode Register for selecting mode
        bus.write_byte_data(Device_Address, Register_mode, 0)
	
	

def read_raw_data(addr):
    
        #Read raw 16-bit value
        high = bus.read_byte_data(Device_Address, addr)
        low = bus.read_byte_data(Device_Address, addr+1)

        #concatenate higher and lower value
        value = ((high << 8) | low)

        #to get signed value from module
        if(value > 32768):
            value = value - 65536
        return value


bus = smbus.SMBus(1) 	# or bus = smbus.SMBus(0) for older version boards
Device_Address = 0x1e   # HMC5883L magnetometer device address

Magnetometer_Init()     # initialize HMC5883L magnetometer 

print (" Reading Heading Angle")

try:
        while True:

                #Read Accelerometer raw value
                x = read_raw_data(X_axis_H)
                y = read_raw_data(Y_axis_H)
                z = read_raw_data(Z_axis_H)
                
                xH_List.append(x)
                yH_List.append(y)

                print("x=%f" %x, "\tz=%f" %y)

                sleep(.1)
        
except KeyboardInterrupt:
        
        xmax = max(xH_List)
        xmin = min(xH_List)
        ymax = max(yH_List)
        ymin = min(yH_List)
        
        xOffset = (xmax + xmin)/2
        yOffset = (ymax + ymin)/2
        
        print(xOffset)
        print(yOffset)
        
        for x in xH_List :
            xH_cList.append(x - xOffset)
        for y in yH_List :
            yH_cList.append(y - yOffset)
        
        plt.scatter(xH_cList, yH_cList, color = 'b')
        plt.scatter(xH_List, yH_List, color = 'r')
        plt.show()
