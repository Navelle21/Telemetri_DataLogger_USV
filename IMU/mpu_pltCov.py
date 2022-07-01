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

print("ACCELEROMETER CALIBRATION")
print('-'*50)

for i in range(200):
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
	
print("CALIBRATION DONE")
print('-'*50)

#Offset based on averaging 200 data sample 
Ax_Offset = sum_Ax/200
Ay_Offset = sum_Ay/200
Az_Offset = 16384-(sum_Az/200)

print("Ay Offset :", Ay_Offset)

SumOfAx = 0
SumOfAy = 0
SumOfAz = 0

#sampling parameter
counter = 0
NumOfSample = 20
dt = 0.01

#velocity initial value
vx_PresentVal = 0
vy_PresentVal = 0
vx_PreviousVal = 0
vy_PreviousVal = 0

#Acceleration initial value
Ay_PreviousVal = 0
Ax_PreviousVal = 0
Ax_ExpectedVal = 0
Ay_ExpectedVal = 0
Az_ExpectedVal = 0

#px, py
px = 0
py = 0

#lists for plotting purpose
axList = []
ayList = []
vxList = []
vyList = []
pxList = []
pyList = []

#lists for storing temporary measurement
Ax_temp = []
Ay_temp = []

#covariance/covariance
Ax_Variance = 0
Ay_Variance = 0

#Exponential filter param
St_PresentVal = 0
St_PreviousVal = 0
Trend_PresentVal = 0
Trend_PreviousVal = 0
alpha = 0.5
betha = 0.9

try:

	#t0 = time()
	while True:
		#Read Accelerometer raw value
		Ax_Raw = read_raw_data(ACCEL_XOUT_H)
		Ay_Raw = read_raw_data(ACCEL_YOUT_H)
		Az_Raw = read_raw_data(ACCEL_ZOUT_H)

		#calculate acceleration in m/s^2 with +/-2g sensitivity
		Ax_Measurement = ((Ax_Raw - Ax_Offset)/16384)*9.8
		Ay_Measurement = ((Ay_Raw - Ay_Offset)/16384)*9.8
		Az_Measurement = ((Az_Raw + Az_Offset)/16384)*9.8

		#sample 20 data (NumofSample) and then calulcate variances, predictions for each cycle
		if counter < NumOfSample:
			SumOfAx = SumOfAx + Ax_Measurement
			SumOfAy = SumOfAy + Ay_Measurement
			SumOfAz = SumOfAz + Az_Measurement

			#storing measurement for calulating variance/covariance purpose
			Ax_temp.append(Ax_Measurement)
			Ay_temp.append(Ay_Measurement)
			counter+=1
		else:

			#calculate Expected Value
			Ax_ExpectedVal = (SumOfAx/NumOfSample) 
			Ay_ExpectedVal = (SumOfAy/NumOfSample)
			Az_ExpectedVal = Az_Measurement

			#reset sum of acceleration
			SumOfAx = 0
			SumOfAy = 0
			SumOfAz = 0

			#calculate variance
			for Measurement in Ax_temp:
				Ax_Variance = Ax_Variance + (Ax_ExpectedVal - Measurement)**2
			Ax_Variance = Ax_Variance/len(Ax_temp)

			for Measurement in Ay_temp:
				Ay_Variance = Ay_Variance + (Ay_ExpectedVal - Measurement)**2
			Ay_Variance = Ay_Variance/len(Ay_temp)

			if Ax_Variance < 0.01:
				Ax_ExpectedVal = 0
				vx_PresentVal = 0
				
			if Ay_Variance < 0.01:
				Ay_ExpectedVal = 0
				vy_PresentVal = 0

			#prediction step
			#calculate the latest velocity
			vx_PresentVal = vx_PresentVal + ((Ax_PreviousVal + Ax_ExpectedVal)/2)*dt
			vy_PresentVal = vy_PresentVal + ((Ay_PreviousVal + Ay_ExpectedVal)/2)*dt
		
			#Exponential Filter
			#vx_presentVal = St_PresentVal + Trend_PresentVal
			#Trend = vx_PresentVal - vx_PreviousVal
			#St_PresentVal = alpha * vx_PresentVal + (1-alpha) *  

			#calculate latest position
			#px = px + ((vx_PreviousVal + vx_PresentVal)/2)*dt
			#py = py + ((vy_PreviousVal + vy_PresentVal)/2)*dt
			px = px + vx_PresentVal * dt + 0.5 * Ax_ExpectedVal * dt* dt
			py = py + vy_PresentVal * dt + 0.5 * Ay_ExpectedVal * dt* dt

			#update the last acceleration
			Ax_PreviousVal = Ax_ExpectedVal
			Ay_PreviousVal = Ay_ExpectedVal

			#update the last velocity
			vx_PreviousVal = vx_PresentVal
			vy_PreviousVal = vy_PresentVal

			#clearing temporary sensor list of sample
			Ax_temp.clear()
			Ay_temp.clear()

			#calculating sensor sampling rate
			#t = round(time()-t0, 2)
			#t0 = time()
			#print(round(t, 3))

			#printing for debugging purpose
			#print("\tAx=%.2f m/s^2" %Ax_ExpectedVal, 
			#		"\tAy=%.2f m/s^2" %Ay_ExpectedVal, 
			#		"\tAz=%.2f m/s^2" %Az_ExpectedVal, 
			#		"\tVx=%.2f m/s" %vx_PresentVal, 
			#		"\tVy=%.2f m/s" %vy_PresentVal, 
			#		"\tpx=%.2f m" %px, 
			#		"\tpy=%.2f m" %py) 

			print("variance Ax = %.5f" %Ax_Variance, "\tvariance Ay = %.5f" %Ay_Variance)
			#for plotting purpose
			#print("px : %.3f" %px, "py : %.3f" %py)
			axList.append(Ax_ExpectedVal)
			ayList.append(Ay_ExpectedVal)
			vxList.append(vx_PresentVal)
			vyList.append(vy_PresentVal)
			pxList.append(px)
			pyList.append(py)

			counter = 0
			
		
except KeyboardInterrupt:
	plt.subplot(231)
	axt = np.linspace(0,len(axList)+1, len(axList))
	axPlt = plt.plot(axt, axList, color='r', label="acceleration-x")
	plt.legend()

	plt.subplot(232)
	vxt = np.linspace(0, len(vxList)+1, len(vxList))
	vxPlt = plt.plot(vxt, vxList, color='b', label="velocity-x")
	plt.legend()
	
	plt.subplot(233)
	pxt = np.linspace(0, len(pxList)+1, len(pxList))
	pxPlt = plt.plot(pxt, pxList, color='g', label="position-x")
	plt.legend()
	
	plt.subplot(234)
	ayt = np.linspace(0, len(ayList)+1, len(ayList))
	ayPlt = plt.plot(ayt, ayList, color='r', label="acceleration-y")
	plt.legend()

	plt.subplot(235)
	vyt = np.linspace(0, len(vyList)+1, len(vyList))
	vyPlt = plt.plot(vyt, vyList, color='b', label="velocity-y")
	plt.legend()

	plt.subplot(236)
	pyt = np.linspace(0, len(pyList)+1, len(pyList))
	pyPlt = plt.plot(pyt, pyList, color='g', label="position-y")
	plt.legend()
	
	plt.suptitle("data sensor pembulatan 1 angka di belakang koma, expected value dari 20 data, bergerak 30cm")
	plt.show()
