import smbus			#import SMBus module of I2C
from time import sleep, time      #import
import matplotlib.pyplot as plt
import numpy as np

#some MPU6050 Registers and their Address
PWR_MGMT_1   = 0x6B
SMPLRT_DIV   = 0x19
CONFIG       = 0x1A
GYRO_CONFIG  = 0x1B
INT_ENABLE   = 0x38
ACCEL_XOUT_H = 0x3B
ACCEL_YOUT_H = 0x3D
ACCEL_ZOUT_H = 0x3F
GYRO_XOUT_H  = 0x43
GYRO_YOUT_H  = 0x45
GYRO_ZOUT_H  = 0x47


def MPU_Init():
	#write to sample rate register
	bus.write_byte_data(Device_Address, SMPLRT_DIV, 7)
	
	#Write to power management register
	bus.write_byte_data(Device_Address, PWR_MGMT_1, 1)
	
	#Write to Configuration register
	bus.write_byte_data(Device_Address, CONFIG, 0)
	
	#Write to Gyro configuration register
	bus.write_byte_data(Device_Address, GYRO_CONFIG, 24)
	
	#Write to interrupt enable register
	bus.write_byte_data(Device_Address, INT_ENABLE, 1)

	#bus.write_byte_data(Device_Address, 0x7D, )


def read_raw_data(addr):
	#Accelero and Gyro value are 16-bit
        high = bus.read_byte_data(Device_Address, addr)
        low = bus.read_byte_data(Device_Address, addr+1)
    
        #concatenate higher and lower value
        value = ((high << 8) | low)
        
        #to get signed value from mpu6050
        if(value > 32768):
                value = value - 65536
        return value


bus = smbus.SMBus(1) 	# or bus = smbus.SMBus(0) for older version boards
Device_Address = 0x68   # MPU6050 device address

MPU_Init()

sleep(1)

print (" Reading Data of Gyroscope and Accelerometer")
sum_Az = 0
sum_Ax = 0
sum_Ay = 0


#list to store measurement summation
Ax_s = []
Ay_s = []
Az_s = []

print("KALIBRASI ACCELEROMETER")
print('-'*50)

for i in range(51):
	#Read Accelerometer raw value
	acc_x = read_raw_data(ACCEL_XOUT_H)
	acc_y = read_raw_data(ACCEL_YOUT_H)
	acc_z = read_raw_data(ACCEL_ZOUT_H)

	#calculate summation
	sum_Ax = sum_Ax + acc_x
	sum_Ay = sum_Ay + acc_y
	sum_Az = sum_Az + acc_z

	#store data for averaging
	Ax_s.append(acc_x)
	Ay_s.append(acc_y)
	Az_s.append(acc_z)

	print("\tAx=%.2f g" %acc_x, "\tAy=%.2f g" %acc_y, "\tAz=%.2f g" %acc_z) 	
	
print("PROSES KALIBRASI SELESAI")
print('-'*50)

avg_Ax = sum_Ax/51
avg_Ay = sum_Ay/51
avg_Az = 16384-(sum_Az/51)

Ax = 0
Ay = 0
Az = 0
counter = 0
dt = 0.03

#vx
vx = 0
Ax0 = 0

#vy
vy = 0
Ay0 = 0

#px, py
px = 0
py = 0

t0=time()
while True:
	#Read Accelerometer raw value
	acc_x = read_raw_data(ACCEL_XOUT_H)
	acc_y = read_raw_data(ACCEL_YOUT_H)
	acc_z = read_raw_data(ACCEL_ZOUT_H)

	#calculate acceleration
	Ax_hat = ((acc_x-avg_Ax)/16384)*9.8
	Ay_hat = ((acc_y-avg_Ay)/16384)*9.8
	Az_hat = ((acc_z+avg_Az)/16384)*9.8

	if counter<10:
		Ax = Ax + Ax_hat
		Ay = Ay + Ay_hat
		#Az = Az + Az_hat
		counter+=1
	else:
		#t = time()-t0
		Ax = Ax/10
		Ay = Ay/10
		Az = Az_hat
		counter = 0

		#trapezoidal integral + low pass filter
		vx = vx + ((Ax0+Ax)/2)*dt
		Ax0 = Ax

		#trapezoidal integral + low pass filter
		vy = vy + ((Ay0+Ay)/2)*dt
		Ay0 = Ay
		
		#calculate latest position
		px = px + vx*dt + 0.5*Ax*dt*dt
		py = py + vy*dt + 0.5*Ay*dt*dt

		
#		print("\tpx=%.2f m"%px, "\tpy=%.2f m"%py)
		print("\tAx=%.2f m/s^2" %Ax, "\tAy=%.2f m/s^2" %Ay, "\tAz=%.2f m/s^2" %Az, "\tVx=%.2f m/s"%vx, "\tVy=%.2f m/s"%vy, "\tpx=%.2f m"%px, "\tpy=%.2f m"%py) 
		#t0 = time()
		#print(t)


