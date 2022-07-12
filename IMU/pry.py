import smbus			#import SMBus module of I2C
from time import sleep, time      #import
import matplotlib.pyplot as plt
import numpy as np
import math
from gpiozero import LED

led = LED(27)

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

#some MPU6050 Registers and their Address
Register_A     = 0              #Address of Configuration register A
Register_B     = 0x01           #Address of configuration register B
Register_mode  = 0x02           #Address of mode register

X_axis_H    = 0x03              #Address of X-axis MSB data register
Z_axis_H    = 0x05              #Address of Z-axis MSB data register
Y_axis_H    = 0x07              #Address of Y-axis MSB data register
declination = -0.00669          #define declination angle of location where measurement going to be done
pi          = 3.14159265359     #define pi value

def read_rawMag_data(addr):
    
        #Read raw 16-bit value
        high = bus.read_byte_data(mag_Address, addr)
        low = bus.read_byte_data(mag_Address, addr+1)

        #concatenate higher and lower value
        value = ((high << 8) | low)

        #to get signed value from module
        if(value > 32768):
            value = value - 65536
        return value

def Magnetometer_Init():
        #write to Configuration Register A
        bus.write_byte_data(mag_Address, Register_A, 0x70)

        #Write to Configuration Register B for gain
        bus.write_byte_data(mag_Address, Register_B, 0xa0)

        #Write to mode Register for selecting mode
        bus.write_byte_data(mag_Address, Register_mode, 0)

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
mag_Address = 0x1e   # HMC5883L magnetometer device address

MPU_Init()
Magnetometer_Init()     # initialize HMC5883L magnetometer 

sleep(1)

print (" Reading Data of Gyroscope and Accelerometer")
sum_Az = 0
sum_Ax = 0
sum_Ay = 0

sum_Gx = 0
sum_Gy = 0
sum_Gz = 0

#list to store measurement summation
Ax_s = []
Ay_s = []
Az_s = []

def orientationCal():
        xAngleOffset = 0
        yAngleOffset = 0

        for i in range(200):
                #Read Accelerometer raw value
                Ax_Raw = read_raw_data(ACCEL_XOUT_H)
                Ay_Raw = read_raw_data(ACCEL_YOUT_H)
                Az_Raw = read_raw_data(ACCEL_ZOUT_H)

                #calculate acceleration in m/s^2 with +/-2g sensitivity
                Ax_Measurement = ((Ax_Raw - Ax_Offset)/16384)
                Ay_Measurement = ((Ay_Raw - Ay_Offset)/16384)
                Az_Measurement = ((Az_Raw + Az_Offset)/16384)


                xAngleOffset = xAngleOffset + math.atan(Ay_Measurement/math.sqrt(Ax_Measurement**2 + Az_Measurement**2)) * 180 / pi
                yAngleOffset = yAngleOffset + math.atan(-1 * Ax_Measurement/math.sqrt(Ay_Measurement**2 + Az_Measurement**2)) * 180 / pi

                
        xAngleOffset = xAngleOffset/200
        yAngleOffset = yAngleOffset/200

        return xAngleOffset, yAngleOffset

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

	#Read Gyroscope raw value
	gyro_x = read_raw_data(GYRO_XOUT_H)
	gyro_y = read_raw_data(GYRO_YOUT_H)
	gyro_z = read_raw_data(GYRO_ZOUT_H)

	Gx = gyro_x
	Gy = gyro_y
	Gz = gyro_z

	sum_Gx = sum_Gx + Gx
	sum_Gy = sum_Gy + Gy
	sum_Gz = sum_Gz + Gz

	#store data for averaging
	Ax_s.append(acc_x)
	Ay_s.append(acc_y)
	Az_s.append(acc_z)

   
	print("\tAx=%.2f g" %acc_x, "\tAy=%.2f g" %acc_y, "\tAz=%.2f g" %acc_z, "\tGx=%.2f" %Gx, "\tGy=%.2f" %Gy) 	
	
print("CALIBRATION DONE")
print('-'*50)

#Offset based on averaging 200 data sample 
Ax_Offset = sum_Ax/200
Ay_Offset = sum_Ay/200
Az_Offset = 16384-(sum_Az/200)

Gx_Offset = sum_Gx/200
Gy_Offset = sum_Gy/200
Gz_Offset = sum_Gz/200

print("Ay Offset=%.2f" %Ay_Offset, "\tAx Offset=%.2f" %Ax_Offset, "\tGx Offset=%.2f" %Gx_Offset, "\tGy Offset=%.2f" %Gy_Offset)

AxAngleOffset, AyAngleOffset = orientationCal()

print("AxAngleOffset : %.4f" %AxAngleOffset, "\tAyAngleOffset : %.4f" %AyAngleOffset)

SumOfAx = 0
SumOfAy = 0
SumOfAz = 0

#sampling parameter
counter = 0
NumOfSample = 20
dt = 0.02

#Acceleration initial value
Ay_PreviousVal = 0
Ax_PreviousVal = 0
Ax_ExpectedVal = 0
Ay_ExpectedVal = 0
Az_ExpectedVal = 0

#lists for plotting purpose
axList = []
ayList = []
vxList = []
vyList = []
pxList = []
pyList = []
QList = []

#lists for storing temporary measurement
Ax_temp = []
Ay_temp = []
Gx_temp = []
Gy_temp = []
Gz_temp = []

#covariance/covariance
Axy_Covariance = 0
Vxy_Covariance = 0
GyroCovariance = 0

#kalman filter model prediction
state = np.array([0,0,0,0])
F = np.array([[1,0,dt,0],
			  [0,1,0,dt],
			  [0,0,1,0],
			  [0,0,0,1]])
			
G = np.array([[0.5*dt**2,0],
			  [0,0.5*dt**2],
			  [dt,0],
			  [0,dt]])
Ax_Angle = 0
Ay_Angle = 0
gyroAngleX = 0
gyroAngleY = 0

counter = 0

Gx_Measurement = 0
Gy_Measurement = 0
Gz_Measurement = 0

sumOfGx = 0
sumOfGy = 0
sumOfGz = 0

#t0 = time()
while True:
    
        #Read magnetometer raw value
        x = read_rawMag_data(X_axis_H)
        z = read_rawMag_data(Z_axis_H)
        y = read_rawMag_data(Y_axis_H)

        #Read Accelerometer raw value
        Ax_Raw = read_raw_data(ACCEL_XOUT_H)
        Ay_Raw = read_raw_data(ACCEL_YOUT_H)
        Az_Raw = read_raw_data(ACCEL_ZOUT_H)

        #calculate acceleration in m/s^2 with +/-2g sensitivity
        Ax_Measurement = ((Ax_Raw - Ax_Offset)/16384)
        Ay_Measurement = ((Ay_Raw - Ay_Offset)/16384)
        Az_Measurement = ((Az_Raw + Az_Offset)/16384)

        #Read Gyroscope raw value
        gyro_x = read_raw_data(GYRO_XOUT_H)
        gyro_y = read_raw_data(GYRO_YOUT_H)
        gyro_z = read_raw_data(GYRO_ZOUT_H)

        #calculate gyro in deg/sec
        Gx_Measurement = (gyro_x - Gx_Offset)/131
        Gy_Measurement = (gyro_y - Gy_Offset)/131
        Gz_Measurement = (gyro_z - Gz_Offset)/131
        if counter < 20:
                sumOfGx = sumOfGx + Gx_Measurement
                sumOfGy = sumOfGy + Gy_Measurement
                sumOfGz = sumOfGz + Gz_Measurement
                counter +=1

                Gx_temp.append(sumOfGx)
                Gy_temp.append(sumOfGy)
                Gz_temp.append(sumOfGz)
        else:

                Gx_ExpectedVal = sumOfGx/20
                Gy_ExpectedVal = sumOfGy/20
                Gz_ExpectedVal = sumOfGz/20

                for (Gx_Measurement, Gy_Measurement) in zip(Gx_temp, Gy_temp):
                        GyroCovariance = GyroCovariance + (Gx_ExpectedVal - Gx_Measurement) * (Gy_ExpectedVal - Gy_Measurement)
                GyroCovariance = GyroCovariance/len(Gx_temp)

                sumOfGx = 0
                sumOfGy = 0
                sumOfGx = 0

                Ax_Angle = 0.5 * Ax_Angle + 0.5 * (math.atan(Ay_Measurement/math.sqrt(Ax_Measurement**2 + Az_Measurement**2)) * 180 / pi - AxAngleOffset)
                Ay_Angle = 0.5 * Ay_Angle + 0.5 * (math.atan(-1 * Ax_Measurement/math.sqrt(Ay_Measurement**2 + Az_Measurement**2)) * 180 / pi - AyAngleOffset)

                gyroAngleX = gyroAngleX + (Gx_ExpectedVal * 0.03 * 8)
                gyroAngleY = gyroAngleY + (Gy_ExpectedVal * 0.03 * 7.5)

                pitch = 0.5 * gyroAngleX + 0.5 * Ax_Angle
                roll = 0.5 * gyroAngleY + 0.5 * Ay_Angle

                if abs(GyroCovariance) < 0.02:
                        Gx_ExpectedVal = 0
                        Gy_ExpectedVal = 0
                        GyroAngleX = 0
                        GyroAngleY = 0
                        pitch = 0
                        roll = 0

                print(#"Ax : %.2f" %Ax_Measurement, 
                        #"\tAy : %.2f" %Ay_Measurement,
                        #"\tGx : %.2f" %Gx_ExpectedVal, 
                        #"\tGy : %.2f" %Gy_ExpectedVal, 
                        #"\tAxAngle : %.2f" %Ax_Angle, 
                        #"\tAyAngle : %.2f" %Ay_Angle,
                        "\tGxAngle : %5.2f" %gyroAngleX,
                        "\tGyAngle : %5.2f" %gyroAngleY, 
                        "\tpitch : %5.2f" %pitch,
                        "\troll : %5.2f" %roll)

                print("Gyro Covariance : %.3f" %GyroCovariance)
        
                Gx_temp.clear()
                Gy_temp.clear()
                Gz_temp.clear()

                counter = 0
                #td = time() - t0
                #t0 = time()
                #print("time : %f" %td)
