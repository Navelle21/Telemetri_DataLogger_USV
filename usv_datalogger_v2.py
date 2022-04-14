#******************************************************************************
# * @file           : DataLogger.py
# * @brief          : Main program body
# ******************************************************************************

import Adafruit_CharLCD as LCD
from gpiozero import Button, LED
from time import sleep, time
import serial
import pynmea2
from geopy import distance
import datetime
import pytz
import csv
from loggerUI import menu, optionMenu
from threading import Thread, Event, Lock, Timer
from queue import Queue
import numpy as np     
import datetime
import socket


#lcd pins
lcd_rs=4
lcd_en=17
lcd_d4=18
lcd_d5=22
lcd_d6=27
lcd_d7=23
lcd_columns=16
lcd_rows=2

#lcd constructor
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows)

#Inisialisasi push button
button_right=Button(5)
button_left=Button(6)
button_ok=Button(25)
button_back=Button(24)

g_LoggerIndicator=LED(12)#led indikator saat sistem mulai logging

#Port Serial GPS    
PORT_GPS = "/dev/ttyS0"
BAUD_GPS = 4800

#Objek untuk terhubung ke port serial
sReceivedPosition = serial.Serial(PORT_GPS, BAUD_GPS, timeout=0.5)

#Tampilan LCD pada startup program
def IntroLCD():
    lcd.set_cursor(7,0)
    lcd.message("USV")
    lcd.set_cursor(3,1)
    lcd.message("Data Logger")
    sleep(2)
    lcd.clear()
    sleep(1)

#deklarasi objek menu tampilan LCD
menu_start = menu(
    subMenu1='Start Logger', 
    subMenu2='Sampling Mode', 
    subMenu3='GPS Info',
    right_button=button_right,
    left_button=button_left, 
    ok_button=button_ok, 
    back_button=button_back, 
    maxPage=3
    )

menu_mode = menu(
    subMenu1='Time', 
    subMenu2='Distance', 
    right_button=button_right, 
    left_button=button_left,
    ok_button=button_ok, 
    back_button=button_back, 
    maxPage=2
    )

menu_GPSInfo = menu(
    right_button=button_right, 
    left_button=button_left, 
    ok_button=button_ok, 
    back_button=button_back, 
    maxPage=2
    )

menu_startLogger = menu(
    right_button=button_right, 
    left_button=button_left, 
    ok_button=button_ok, 
    back_button=button_back, 
    maxPage=1
    )

optMenu_time = optionMenu(
    subMenu1='Time', 
    units='s', 
    value=0, 
    maxValue=10, 
    right_button=button_right, 
    left_button=button_left,
    ok_button=button_ok, 
    back_button=button_back
    )

optMenu_dist = optionMenu(
    subMenu1='Distance', 
    units='m', 
    value=0, 
    maxValue=20, 
    right_button=button_right, 
    left_button=button_left,
    ok_button=button_ok, 
    back_button=button_back
    )

#pemberian index pada menu dan submenu UI LCD
g_menuLayer =  {'menu_start':0, 'menu_mode':1, 'optMenu_time':2, 'menu_GPSInfo':3, 'menu_startLogger':4, 'optMenu_dist':5}
g_submenu_start = {'smenu_startLogger':0, 'smenu_mode': 1, 'smenu_GPSInfo':2}
g_submenu_mode = {'stimeSampling':0, 'sdistSampling':1}
g_submenu_GPSInfo = {'coordinate':0, 'time_and_speed':1}

#Variable mode sempling : time interval, distance interval
g_samplingModeDict = {'timeInterval':0, 'distInterval':1}
g_samplingMode = g_samplingModeDict['timeInterval']

#nilai interval dari sampling : time interval, distance interval
g_samplingTime = 0
g_samplingDistance = 0

#g_rawGpsData = [0.0, 0.0, 0.0, 0.0, 0.0]

#flag yang digunakan untuk sinkronisasi antar Thread
g_startSamplingTimeflag = False
g_startLoggingflag = False
g_startSamplingDistflag = False
g_TCPDepthConnect = False

#struktur FIFO buffer untuk menampung data dari sensor
g_GprmcBuffer = Queue()
g_DptBuffer = Queue()
g_GprmcRawData = [0.0, 0.0, 0.0, datetime.time(0,0,0)]

#variable waktu awal dan akhir untuk menghitung interval waktu pada saat sampling data
g_prevTime = datetime.time(0,0,0)
g_currTime = datetime.time(0,0,0)

#connect to echosounder NMEASimulator132 via TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    sock.connect(("127.0.0.1", 3000))
    g_TCPDepthConnect = True
    print("Successful Connection")
except:
    print("Connection Failed")

#@brief fnUserInterface()
#   DaftarMenu : 
#   1. menuIndex 0 : menu_start
#      @submenuIndex menu_start : 
#      submenuIndex 1 : StartLogger
#      submenuIndex 2 : Sampling Mode/menu_mode
#      submenuIndex 3 : GPS Info
#
#   2. menuIndex 4 : menu_startLogger/StartLogger (submenu 1 dari menu_start no 1)
#      @submenuIndex menu_startLogger : belum ada
#      menu 4 digunakan untuk mengsinkronisasi antar thread pengambilan data
#       
#   3. menunIdex 1 : menu_mode/Sampling Mode (submenu 2 dari menu_start no 1)
#      @submenuIndex menu_mode :
#      submenuIndex 0 : optMenu_time (subMenu untuk setting parameter sampling time)
#      submenuIndex 1 : optMenu_dist (subMenu untuk setting parameter sampling distance)
#   
#   4. menuIndex 3 : menu_GPSInfo/GPS Infor (submenu 3 dari menu_start no 1)
#      @submenu : @submenuIndex optMenu_time : 
#      submenuIndex 0 : coordinate (berisi keterangan latitude, dan longitude)
#      submenuIndex 1 : time_and_speed (berisi keterangan kecepatan dan waktu UTC)
#
#   5. menuIndex 2 : optMenu_time (submenu 0 dari menu_mode/Sampling Mode)
  
def fnUserInterface(): 
    global g_samplingMode
    global g_samplingDistance
    global g_LoggerIndicator
    global g_samplingTime 
    global g_samplingModeDict
    global g_menuLayer
    global g_startSamplingDistflag
    global g_startSamplingTimeflag
    global rawGpsData 
    
    IntroLCD()#untuk menampilkan intro di lcd (saat device pertama kali dinyalakan)
    
    while True:
        if menu.menuIndex == g_menuLayer['menu_start']: 
            #polling push button
            menu_start.poll_prevButton()
            menu_start.poll_nextButton()
            menu_start.dispMenu()
            #program untuk menampilkan mode sampling yang digunakan
            if menu_start.submenuIndex == g_submenu_start['smenu_mode']: 
                if g_samplingMode == g_samplingModeDict['timeInterval']:
                    lcd.set_cursor(2,1)
                    lcd.message("Mode Time")
                elif g_samplingMode == g_samplingModeDict['distInterval']:
                    lcd.set_cursor(2,1)
                    lcd.message("Mode Dist")
                if menu_start.poll_nextMenuButton() == True:
                    lcd.clear()
                    menu.menuIndex = g_menuLayer['menu_mode']
            #program untuk pindah ke menu_GPSInfo
            if menu_start.submenuIndex == g_submenu_start['smenu_GPSInfo'] and menu_start.poll_nextMenuButton() == True:
                lcd.clear()
                menu.menuIndex = g_menuLayer['menu_GPSInfo'] 
            #program untuk pindah ke menu_startLogger
            if menu_start.submenuIndex == g_submenu_start['smenu_startLogger'] and menu_start.poll_nextMenuButton() == True:
                lcd.clear()
                menu.menuIndex = g_menuLayer['menu_startLogger'] 
        
        elif menu.menuIndex == g_menuLayer['menu_mode']:    
            #polling push button
            menu_mode.poll_prevButton()
            menu_mode.poll_nextButton()
            menu_mode.poll_prevMenuButton(menu_start, 0)
            #program saat di submenu timeSammpling
            if menu_mode.submenuIndex == g_submenu_mode['stimeSampling']:
                if menu_mode.poll_nextMenuButton() == True:
                    #program untuk pindah ke menu optMenu_time untuk setting nilai sampling waktu
                    lcd.clear()
                    menu.menuIndex = g_menuLayer['optMenu_time'] 
                else:
                    #program untuk menampilkan nilai samplilng waktu yang digunakan 
                    lcd.set_cursor(2,1)
                    lcd.message(f"Time {g_samplingTime}s")
            #program saat di submenu distance Sampling
            elif menu_mode.submenuIndex == g_submenu_mode['sdistSampling']: 
                if menu_mode.poll_nextMenuButton() == True:
                    #program untuk pindah ke menu optMenu_dist untuk setting nilai sampling jarak
                    lcd.clear()
                    menu.menuIndex = g_menuLayer['optMenu_dist']
                else:
                    #program untuk menampilkan nilai sampling jarak yang digunakan 
                    lcd.set_cursor(2,1)
                    lcd.message(f"Dist {g_samplingDistance}m")
            menu_mode.dispMenu()

        elif menu.menuIndex == g_menuLayer['optMenu_time']:  
            #polling push button
            optMenu_time.poll_increaseVal()
            optMenu_time.poll_decreaseVal()
            #program untuk menyimpan nilai sampling waktu yang sudah diubah
            if optMenu_time.poll_saveData(menu_mode)==True:
                lcd.clear()
                g_samplingMode = g_samplingModeDict['timeInterval']
                g_samplingTime = optMenu_time.getVal()
                g_samplingDistance = 0 #reset sampling distance apabila mmode sampling time aktif
                menu.menuIndex = g_menuLayer['menu_mode']
            else:
                optMenu_time.dispMenu()
            optMenu_time.poll_prevMenuButton(menu_mode, 1) #jangan dipindah
        
        elif menu.menuIndex == g_menuLayer['optMenu_dist']:
            #polling push button
            optMenu_dist.poll_increaseVal()
            optMenu_dist.poll_decreaseVal()
            #dibawah ini adalah program untuk save data sampling time yang sudah diset user
            if optMenu_dist.poll_saveData(menu_mode)==True:
                lcd.clear()
                g_samplingMode = g_samplingModeDict['distInterval']
                g_samplingDistance = optMenu_dist.getVal()
                g_samplingTime = 0 #reset sampling time apabila mode sampling distance aktif
                menu.menuIndex = g_menuLayer['menu_mode']
            else:
                optMenu_dist.dispMenu()
            optMenu_dist.poll_prevMenuButton(menu_mode, 1) #jangan dipindah

        elif menu.menuIndex == g_menuLayer['menu_GPSInfo']: 
            #polling push button
            if menu_GPSInfo.poll_prevMenuButton(menu_start, 0)==True:
                lcd.clear()
            menu_GPSInfo.poll_nextButton()
            menu_GPSInfo.poll_prevButton()
            try:
                sData = sReceivedPosition.readline()
                sData = sData.decode("latin-1").strip()
                if sData.find("RMC")>0:
                    GprmcParseResult = pynmea2.parse(sData)
                    #submenu 'coordinate' untuk menampilkan data latitude dan longitude
                    if menu_GPSInfo.submenuIndex == g_submenu_GPSInfo['coordinate']:
                        lcd.set_cursor(0,0)
                        lcd.message(f"lat: {GprmcParseResult.latitude}")
                        lcd.set_cursor(0,1)
                        lcd.message(f"long: {GprmcParseResult.longitude}")
                    #submenu 'time_and_speed' untuk menampilkan data time utc dan speed over ground
                    elif menu_GPSInfo.submenuIndex == g_submenu_GPSInfo['time_and_speed']:
                        lcd.set_cursor(0,0)
                        lcd.message(f"utc: {GprmcParseResult.timestamp}")
                        lcd.set_cursor(0,1)
                        lcd.message(f"speed: {GprmcParseResult.spd_over_grnd} knots") 
            except TypeError:
                pass
            
        elif menu.menuIndex == g_menuLayer['menu_startLogger']:       
            global g_startLoggingflag
            global g_startSamplingTimeflag      
            global g_TCPDepthConnect
            
            while g_TCPDepthConnect == False: #menunggu koneksi tcp
                try:
                    sock.connect(("127.0.0.1", 3000))
                    g_TCPDepthConnect = True
                    print("Successful Connection")
                except:
                    print("Connection Failed")

            #print(g_startSamplingTimeflag)
            g_LoggerIndicator.on()
            if menu_startLogger.poll_prevMenuButton(menu_start, 0)==True:#untuk menghentikan proses data
                g_startSamplingDistflag = False
                g_startSamplingTimeflag = False
                lcd.clear()
                g_LoggerIndicator.off()
            elif g_samplingMode == g_samplingModeDict['timeInterval']:
                g_startSamplingTimeflag = True
                g_startSamplingDistflag = False
            elif g_samplingMode == g_samplingModeDict['distInterval']:
                g_startSamplingTimeflag = False
                g_startSamplingDistflag = True
                g_startGetDepthflag = True
           

def fnReadTime():
    global g_prevTime
    global g_currTime
    global g_startSamplingTimeflag
    global g_GprmcRawData
    global g_startLoggingflag

    if g_startSamplingTimeflag == True:
        sData = sReceivedPosition.readline()
        sData = sData.decode("latin-1").strip()
        if sData.find("RMC")>0:
            try:
                GprmcParseResult = pynmea2.parse(sData)
                g_currTime = GprmcParseResult.timestamp
                #pengecekan interval waktu dari utc gps
                if (g_currTime.second - g_prevTime.second) > 0:
                    if (g_currTime.second - g_prevTime.second) >= g_samplingTime:
                        #proses queueing data gps ke queuebuffer
                        Thread(target=fnGetDepth).start()
                        g_GprmcBuffer.put(GprmcParseResult.timestamp)
                        g_GprmcBuffer.put(GprmcParseResult.latitude)
                        g_GprmcBuffer.put(GprmcParseResult.longitude)
                        g_GprmcBuffer.put(GprmcParseResult.spd_over_grnd)
                        g_prevTime = GprmcParseResult.timestamp
                        g_startLoggingflag = True
                else:
                    if (g_currTime.second+60 - g_prevTime.second) >= g_samplingTime:
                        #proses queueing data gps ke queuebuffer
                        Thread(target=fnGetDepth).start()
                        g_GprmcBuffer.put(GprmcParseResult.timestamp)
                        g_GprmcBuffer.put(GprmcParseResult.latitude)
                        g_GprmcBuffer.put(GprmcParseResult.longitude)
                        g_GprmcBuffer.put(GprmcParseResult.spd_over_grnd)
                        g_prevTime = GprmcParseResult.timestamp
                        g_startLoggingflag = True
            except TypeError:
                pass   
    Thread(target=fnReadTime).start()

def fnStoreData():
    global g_startLoggingflag
    LoggerDataRow = {'timestamp':0, 'latitude':0, 'longitude':0, 'spd_over_grnd':0, 'waterDepth':0} #format urutan data csv

    if g_startLoggingflag == True:
        with open('echologger.csv', 'a+', newline = '') as echologger:
            #proses dequeueing
            if not g_GprmcBuffer.empty():
                for key in LoggerDataRow.keys():
                    if key == 'waterDepth':
                        LoggerDataRow[key] = g_DptBuffer.get()#dequeing dari buffer dpt
                    else:
                        LoggerDataRow[key] = g_GprmcBuffer.get()#dequeing dari buffer gprmc
            fieldnames = ['timestamp', 'latitude', 'longitude', 'spd_over_grnd', 'waterDepth']
            csv_writer = csv.DictWriter(echologger, fieldnames = fieldnames, delimiter = ',')            
            csv_writer.writerow(LoggerDataRow)
            g_startLoggingflag = False
    Timer(0.1, fnStoreData).start()

def fnGetDepth():
    global g_startGetDepthflag
    
    sData = sock.makefile()
    sData = sock.recv(2000)
    sData = sData.decode("utf-8").strip()
    for sLine in sData.splitlines():
        try:
            sRawDptData = sLine.split(",")
            if sRawDptData[0] == "$SDDPT":
                g_DptBuffer.put(np.float64(sRawDptData[1]))
        except ValueError:
            pass

def main():
    tThreadOne = Thread(target=fnUserInterface)
    tThreadTwo = Thread(target=fnReadTime)
    tThreadThree = Thread(target=fnStoreData)
    tThreadOne.start()
    tThreadTwo.start()
    tThreadThree.start()
    tThreadOne.join()
    tThreadTwo.join()
    tThreadThree.join()
   

if __name__=='__main__':
    main()