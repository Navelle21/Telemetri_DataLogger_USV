import FaBo9Axis_MPU9250
from time import time, sleep
import sys #important for mpu9250
import matplotlib.pyplot as plt
import numpy as np
import math
from gpiozero import LED

led = LED(24)

mpu9250 = FaBo9Axis_MPU9250.MPU9250()

mpu9250.configAK8963(mode = 0x06, mfs = 0x01)


#-----------------GLOBAL VARIABLE DECLARATION------------------------#
#variable for accelerometer calibration
sumOfax = 0
sumOfay = 0
sumOfaz = 0
#variable for gyroscope calibration
sumOfgx = 0
sumOfgy = 0
sumOfgz = 0

numOfSampleCal = 1000 #number of sampled data for calibration

#for debugging purpose
ax_temp = []
ay_temp = []
az_temp = []
vx_temp = []
vy_temp = []
px_temp = []
py_temp = []
#for calculating covariance
axRaw_temp = []
ayRaw_temp = []
azRaw_temp = []

covQ = 0

#sampling variable
counter = 0
numOfSample = 20

#prediction model
dt = 0.05
F = np.array([[1, 0, dt, 0],
              [0, 1, 0, dt],
              [0, 0, 1, 0 ],
              [0, 0, 0, 1 ]])

#state = [px, py, vx, vy]
state = np.array([0, 0, 0, 0])

G = np.array([[0.5 * dt**2, 0],
              [0, 0.5 * dt**2],
              [dt, 0],
              [0, dt]])

u_t = np.array([0, 0]) # ax, ay
state_current = state.copy()
#------------------------------------------------------------------#

#----------------------- CALIBRATION CODE--------------------------#
def orientationcal():
    xAngleOffset = 0
    yAngleOffset = 0
    
    accel = mpu9250.readAccel(axOffset, ayOffset, azOffset)

    for i in range(200):
        axRaw = accel['x']
        ayRaw = accel['y']
        azRaw = accel['z']
    
        xAngleOffset = xAngleOffset + math.atan(ayRaw/math.sqrt(axRaw**2 + azRaw**2)) * 180 / math.pi
        yAngleOffset = yAngleOffset + math.atan(-1 * axRaw/math.sqrt(ayRaw**2 + azRaw**2)) * 180 / math.pi
    
    xAngleOffset = xAngleOffset/200
    yAngleOffset = yAngleOffset/200
    
    return xAngleOffset, yAngleOffset

print("ACCELEROMETER & GYRO CALIBRATION")
print('-'*50)

for i in range(numOfSampleCal):
    #read raw accelerometer data
    accel = mpu9250.readRawAccel()
    axRaw = accel['x']
    ayRaw = accel['y']
    azRaw = accel['z']
    
    gyro = mpu9250.readRawGyro()
    gxRaw = gyro['x']
    gyRaw = gyro['y']
    gzRaw = gyro['z']

    #summing all of read accelerometer data
    sumOfax = sumOfax + axRaw
    sumOfay = sumOfay + ayRaw
    sumOfaz = sumOfaz + azRaw
    
    #summing all of read gyro data
    sumOfgx = sumOfgx + gxRaw
    sumOfgy = sumOfgy + gyRaw
    sumOfgz = sumOfgz + gzRaw

#Accelerometer Measurement Offset
axOffset = sumOfax/numOfSampleCal
ayOffset = sumOfay/numOfSampleCal
azOffset = 16384 - sumOfaz/numOfSampleCal

#Gyroscope Measurement Offset
gxOffset = sumOfgx/numOfSampleCal
gyOffset = sumOfgy/numOfSampleCal
gzOffset = sumOfgz/numOfSampleCal

#reset value
sumOfax = 0
sumOfay = 0
sumOfaz = 0

sumOfgx = 0
sumOfgy = 0
sumOfgz = 0

sumOfH = 0

pitch = 0
roll = 0

heading_angle = 0
#pitch roll yaw calibration
axAngleOffset, ayAngleOffset = orientationcal()
        
#for debugging purpose
print("axOffset : %.3f" %axOffset, "\tayOffset : %.3f" %ayOffset, "\tazOffset : %.3f" %azOffset)
print("gxOffset : %.3f" %gxOffset, "\tgyOffset : %.3f" %gyOffset, "\tgzOffset : %.3f" %gzOffset)
print("axAngleOffset : %.3f" %axAngleOffset, "ayAngleOffset : %.3f" %ayAngleOffset)
sleep(1)

#---------------------------------------------------------------------------------------------#

#t0 = time()
while True:
    accel = mpu9250.readAccel(axOffset, ayOffset, azOffset)
    axRaw = accel['x'] * 9.8
    ayRaw = accel['y'] * 9.8
    azRaw = accel['z'] * 9.8
    
    #print("ax : %.2f" %axRaw, "\tay : %.2f" %ayRaw, "\taz : %.2f" %azRaw)
    
    gyro = mpu9250.readGyro(gxOffset, gyOffset, gzOffset)
    gxRaw = gyro['x']
    gyRaw = gyro['y']
    gzRaw = gyro['z']
    
    #print("gx : %.3f" %gxRaw, "gy : %.3f" %gyRaw, "gz : %.3f" %gzRaw)
    
    if counter <= numOfSample:
        sumOfax = sumOfax + axRaw
        sumOfay = sumOfay + ayRaw
        sumOfaz = sumOfaz + azRaw
        
        #for calculating covariance purpose
        axRaw_temp.append(axRaw)
        ayRaw_temp.append(ayRaw)
        
        sumOfgx = sumOfgx + gxRaw
        sumOfgy = sumOfgy + gyRaw
        sumOfgz = sumOfgz + gzRaw
        
        #counting sample measurement
        counter +=1
    else:
        axExpectedVal = sumOfax / numOfSample
        ayExpectedVal = sumOfay / numOfSample
        azExpectedVal = azRaw
        
        gxExpectedVal = sumOfgx / numOfSample
        gyExpectedVal = -(sumOfgy / numOfSample)
        gzExpectedVal = sumOfgz / numOfSample
                       
        #calculating accelerometer angle
        axAngle = math.atan(ayRaw/math.sqrt(axRaw**2 + azRaw**2)) * 180 / math.pi
        ayAngle = -(math.atan(-1 * axRaw/math.sqrt(ayRaw**2 + azRaw**2)) * 180 / math.pi)
        
        #print("axAngle : %.3f" %axAngle, "ayAngle : %.3f" %ayAngle)
        
        roll = round((0.9 * (roll + gxExpectedVal * dt) + 0.1 * axAngle),1)
        pitch = round((0.9 * (pitch + gyExpectedVal * dt) + 0.1 * ayAngle),1)
        
        #print("gx : %3.f" %gxExpectedVal, "gy : %.3f" %gyExpectedVal)
        print("pitch : %.3f" %pitch, "roll : %.3f" %roll) 
        
        mag = mpu9250.readMagnet()
        xmag = mag['x']
        ymag = mag['y']
        zmag = mag['z']
        
        cxmag = 0.078899*(xmag-13.438828) -0.000369*(ymag-69.004584) -0.000026*(zmag+33.913730)
        cymag = -0.000369*(xmag-13.438828) + 0.077155*(ymag-69.004584) + 0.003212*(zmag+33.913730)
        czmag = -0.000026*(xmag-13.438828) + 0.003212*(ymag-69.004584) +0.082193*(zmag+33.913730)
        
        xH = cxmag*math.cos(pitch) + cymag*math.sin(roll)*math.sin(pitch) - czmag*math.cos(roll)*math.sin(pitch)
        yH = cymag*math.cos(roll) + czmag*math.sin(roll)
        
        #print("xH: %d" %xH, "yH: %d" %yH)
        heading = math.atan2(xH, yH)

        #Due to declination check for >360 degree
        #if(heading > 2*math.pi):
        #    heading = heading - 2*math.pi

        #check for sign
        #if(heading < 0):
        #    heading = heading + 2*math.pi
                
        #convert into angle
        #heading_angle = int(heading * 180/math.pi)
        heading_angle = int(0.9*heading_angle + 0.1*heading / (2*math.pi) * 360)
        print("heading : %.2f" %heading_angle)
        
        if abs(heading_angle) < 5:
            led.on()
        else:
            led.off()
            
        #reset value 
        sumOfax = 0
        sumOfay = 0
        sumOfaz = 0
        
        sumOfgx = 0
        sumOfgy = 0
        sumOfgz = 0
        
     
        

        #covariance calculation
        for axRaw, ayRaw in zip(axRaw_temp, ayRaw_temp):
            covQ = covQ + (axExpectedVal - axRaw) * (ayExpectedVal - ayRaw)
        covQ = covQ/len(axRaw_temp)

        if abs(covQ) < 0.0001:
            axExpectedVal = 0
            ayExpectedVal = 0
            state_current[2] = 0
            state_current[3] = 0

        u_t = np.array([axExpectedVal, ayExpectedVal])
        predicted_state = F @ state_current + G @ u_t
        state_current = predicted_state

        #clear raw data list
        axRaw_temp.clear()
        ayRaw_temp.clear()

        counter = 0

        #print for debugging purpose
        #print("ax : %.2f" %u_t[0], "\tay : %.2f" %u_t[1])
        #print(covQ)

        #for plotting purpose
        ax_temp.append(axExpectedVal)
        ay_temp.append(ayExpectedVal)
        vx_temp.append(predicted_state[2])
        vy_temp.append(predicted_state[3])
        px_temp.append(predicted_state[0])
        py_temp.append(predicted_state[1])
        #td = time() - t0
        #t0 = time()
        #print(td)
