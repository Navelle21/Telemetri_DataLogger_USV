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
import utm
import math

######################LCD CONFIGURATION######################
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

######################PUSH BUTTON CONFIGURATION######################
#Inisialisasi push button
button_right=Button(25)#5
button_left=Button(24)#6
button_ok=Button(5)#25
button_back=Button(6)#24

######################LED INDICATOR######################
g_LoggerIndicator=LED(12)#led indikator saat sistem mulai logging
g_ErrorIndicator=LED(26)
g_LoggingIndicator=LED(13)

#Port Serial GPS    
PORT_GPS = "/dev/ttyS0"
BAUD_GPS = 9600

#Objek untuk terhubung ke port serial
sReceivedPosition = serial.Serial(PORT_GPS, BAUD_GPS, timeout=0.2)

######################Tampilan LCD pada startup program######################
def IntroLCD():
    lcd.set_cursor(7,0)
    lcd.message("USV")
    lcd.set_cursor(3,1)
    lcd.message("Data Logger")
    sleep(2)
    lcd.clear()
    sleep(1)

######################deklarasi objek menu tampilan LCD######################
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
    right_button=button_left, 
    left_button=button_right,
    ok_button=button_ok, 
    back_button=button_back
    )

optMenu_dist = optionMenu(
    subMenu1='Distance', 
    units='m', 
    value=0, 
    maxValue=20, 
    right_button=button_left, 
    left_button=button_right,
    ok_button=button_ok, 
    back_button=button_back
    )
############################################KONFIGURASI ANTARMUKA LCD############################################
#pemberian index pada menu dan submenu UI LCD
g_menuLayer =  {'menu_start':0, 'menu_mode':1, 'optMenu_time':2, 'menu_GPSInfo':3, 'menu_startLogger':4, 'optMenu_dist':5}
g_submenu_start = {'smenu_startLogger':0, 'smenu_mode': 1, 'smenu_GPSInfo':2}
g_submenu_mode = {'stimeSampling':0, 'sdistSampling':1}
g_submenu_GPSInfo = {'coordinate':0, 'time_and_speed':1}

#Variable mode sempling : time interval, distance interval
g_samplingModeDict = {'timeInterval':0, 'distInterval':1}
g_samplingMode = g_samplingModeDict['timeInterval']

#nilai interval dari sampling : time interval, distance interval

g_samplingDistance = 0

#g_rawGpsData = [0.0, 0.0, 0.0, 0.0, 0.0]

######################KONFIGURASI SINKRONISASI THREAD######################
#flag yang digunakan untuk sinkronisasi antar Thread
g_startSamplingTimeflag = False
g_startLoggingflag = False
g_startSamplingDistflag = False
g_startGetDepthflag = False
g_logDepth = False
g_TCPDepthConnect = False

g_f64RawData = [datetime.time(0,0,0), 0.0, 0.0, 0, '', 0.0]
g_f64Curr_x = 0.0
g_f64Prev_X = 0.0
g_f64Curr_y = 0.0
g_f64Prev_y = 0.0


######################KONEKSI DATA LOGGER KE DEEPER VIA UDP######################
sock = socket.socket(socket.AF_INET, socket. SOCK_DGRAM)

try:
    sock.bind(("", 10110))
    g_TCPDepthConnect = True
    print("Successful Connection")
except:
    print("Connection Failed")

           
# @brief : Thread untuk ambil data koordinat setiap interval waktu tertentu
# @param : GpggaBuffer adalah FIFO Buffer yang menampung latitude dan longitude
#          lock adalah mutex yang digunakan untuk sinkronisasi antar thread dan mencegah race condition
#          samplingTime adalah parameter sampling rate dalam satuan detik yang dikonfigurasi oleh operator pada main Thread (LCD UI)
# @retval : mengisi data time stamp dan koordinat pada GpggaBuffer 
def fnReadTime(GpggaBuffer, lock, samplingTime):
    global g_startSamplingTimeflag
    global g_startLoggingflag
    global g_logDepth

    prevTime = datetime.time(0,0,0)
    currtime = datetime.time(0,0,0)

    latitude = 0
    longitude = 0
    
    while g_startSamplingTimeflag == True:
        
        sData = sReceivedPosition.readline()
        sData = sData.decode("latin-1").strip()
        if sData.find("GGA")>0:
            
            try:
                GpggaParseResult = pynmea2.parse(sData)
                currtime = GpggaParseResult.timestamp
                #pengecekan interval waktu dari utc gps

                if latitude == 0 and longitude == 0:
                    latitude = GpggaParseResult.latitude
                    longitude = GpggaParseResult.longitude
                elif not GpggaParseResult.latitude == 0 and not GpggaParseResult.longitude == 0:
                    latitude = 0.5*latitude + 0.5*GpggaParseResult.latitude
                    longitude = 0.5*longitude + 0.5*GpggaParseResult.longitude
                    if (currtime.second - prevTime.second) >= samplingTime and g_logDepth == False:
                        with lock:
                            print("found gga")
                            #proses queueing data gps ke queuebuffer                      
                            GpggaBuffer.put(GpggaParseResult.timestamp, block=False, timeout=0.2)
                            GpggaBuffer.put(latitude, block=False, timeout=0.2)
                            GpggaBuffer.put(longitude, block=False, timeout=0.2)
                            prevTime = GpggaParseResult.timestamp
                            
                            g_startLoggingflag = True
                            g_logDepth = True
            
                    elif (currtime.second+60 - prevTime.second) >= samplingTime and g_logDepth == False:
                        #proses queueing data gps ke queuebuffer
                        with lock:
                            GpggaBuffer.put(GpggaParseResult.timestamp, block=False, timeout=0.2)
                            GpggaBuffer.put(latitude, block=False, timeout=0.2)
                            GpggaBuffer.put(longitude, block=False, timeout=0.2)
                            prevTime = GpggaParseResult.timestamp
                            
                            g_logDepth = True
            except: #TypeError:
                print(exception)  

   
# @brief : perhitungan jarak menggunakan euclidean distance
# @param : x1 easting awal, y1 northing awal, x2 easting akhir, y2 northing akhir
def calculateDistance(x1, y1, x2, y2):
   f64_Distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
   return f64_Distance

# @brief : Thread untuk ambil data koordinat setiap interval jarak tertentu
# @param : GpggaBuffer adalah FIFO Buffer yang menampung latitude dan longitude
#          lock adalah mutex yang digunakan untuk sinkronisasi antar thread dan mencegah race condition
#          samplingTime adalah parameter sampling rate dalam satuan detik yang dikonfigurasi oleh operator pada main Thread (LCD UI)
# @retval : mengisi data time stamp dan koordinat pada GpggaBuffer 
def fnReadDistance(GpggaBuffer, lock):
    global g_f64Prev_X
    global g_f64Prev_y
    global g_f64RawData
    global g_startLoggingflag
    global g_startSamplingDistflag
    global g_logDepth
    
    g_f64Curr_x = 0.0
    g_f64Curr_y = 0.0
    latitude = 0
    longitude = 0

    while g_startSamplingDistflag == True:
        #ambil data latitude dan longitude dari gps
        
        sData = sReceivedPosition.readline()
        sData = sData.decode("latin-1").strip()
        if sData.find("GGA")>0:
            sParseResult = pynmea2.parse(sData)
            if latitude == 0 and longitude == 0:
                latitude = sParseResult.latitude
                longitude = sParseResult.longitude
            else:
                latitude = 0.5 * latitude + 0.5 * sParseResult.latitude
                longitude = 0.5 * longitude + 0.5 * sParseResult.longitude
            
            g_f64Curr_x, g_f64Curr_y, __temp__, __temp__ = utm.from_latlon(float(latitude), float(longitude))
            
            if g_f64Prev_X == 0.0 and g_f64Prev_y == 0.0:
                g_f64Prev_X = g_f64Curr_x
                g_f64Prev_y = g_f64Curr_y
            else:
                m_f64_Distance_UTM = calculateDistance(g_f64Curr_x, g_f64Curr_y, g_f64Prev_X, g_f64Prev_y)
                print("distance : %.3f" %m_f64_Distance_UTM)

                if(m_f64_Distance_UTM >= g_samplingDistance):
                    with lock:
                        print("We have reached the next", g_samplingDistance, "m")
                        
                        GpggaBuffer.put(sParseResult.timestamp, timeout=0.2)
                        GpggaBuffer.put(g_f64Curr_x, timeout=0.2)
                        GpggaBuffer.put(g_f64Curr_y, timeout=0.2)
                        
                        
                        g_f64Prev_X = g_f64Curr_x
                        g_f64Prev_y = g_f64Curr_y
                        g_logDepth = True
                            
                        
    
# @brief : Thread untuk penyimpanan data ke SD Card
# @param : lock mutex sinkronisasi , GpggaBuffer FIFO Buffer koordinat dan timestamp utc, DptBuffer FIFO buffer kedalaman air
# @retval : -
def fnStoreData(lock, GpggaBuffer, DptBuffer):
    global g_startLoggingflag
    LoggerDataRow = {'timestamp':0, 'latitude':0, 'longitude':0, 'waterDepth':0} #format urutan data csv
    try:
        with open('echologger8.csv', 'a+', newline = '') as echologger:
            #proses dequeueing
            g_LoggingIndicator.toggle()
            if not GpggaBuffer.empty() :#and not DptBuffer.empty():
                
                for key in LoggerDataRow.keys():
                    if key == 'waterDepth':
                        with lock:
                            LoggerDataRow[key] = DptBuffer.get()#dequeing dari buffer dpt
                    else:
                        with lock:
                            LoggerDataRow[key] = GpggaBuffer.get()#dequeing dari buffer gprmc
                        
                fieldnames = ['timestamp', 'latitude', 'longitude', 'waterDepth']
                csv_writer = csv.DictWriter(echologger, fieldnames = fieldnames, delimiter = ',')   
                with lock:         
                    csv_writer.writerow(LoggerDataRow)
    except:
        print(exception)
                
    
# @brief : Thread pengukuran kedalaman air
# @param : Gpgga Buffer FIFO Buffer koordinat dan timestamp utc, DptBuffer FIFO Buffer kedalaman air, lock mutex sinkronisasi thread
# @retval :-
def fnGetDepth(GpggaBuffer, DptBuffer, lock):
    global g_startGetDepthflag
    global g_logDepth
    

    while g_startGetDepthflag == True:
        if g_logDepth == True:
            with lock:
                DbtDepth, addr = sock.recvfrom(4096)
                DbtDepth = str(DbtDepth).strip()
                
                for sLine in DbtDepth.splitlines():
                    try:
                        sRawData = sLine.split(",")
                        if sRawData[0] == "b'$SDDBT":
                            DptBuffer.put(float(sRawData[3]), timeout=0.2)
                            threadLogger = Thread(name="store data", target=fnStoreData, args=(lock, GpggaBuffer, DptBuffer))
                            threadLogger.start()
                            g_logDepth = False
                    except:# ValueError:
                        print(exception)


#   @brief main Thread()
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
def main():
    global g_samplingMode
    global g_samplingDistance
    global g_LoggerIndicator
    
    global g_samplingModeDict
    global g_menuLayer
    global g_startSamplingDistflag
    global g_startSamplingTimeflag
    global g_startGetDepthflag
    global rawGpsData 
    global g_logDepth
    
    samplingTime = 0

    GpggaBuffer = Queue()
    DptBuffer = Queue()
    lock = Lock()

    startThreadflag = False

    IntroLCD()#untuk menampilkan intro di lcd (saat device pertama kali dinyalakan)
    
    while True:
        
        ##################### MENU START ######################
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
                
         ##################### MENU MODE ######################
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
                    lcd.message(f"Time {samplingTime}s")
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
            
        ##################### MENU PARAMETER INTERVAL WAKTU ######################
        elif menu.menuIndex == g_menuLayer['optMenu_time']:  
            #polling push button
            optMenu_time.poll_increaseVal()
            optMenu_time.poll_decreaseVal()
            #program untuk menyimpan nilai sampling waktu yang sudah diubah
            if optMenu_time.poll_saveData(menu_mode)==True:
                lcd.clear()
                g_samplingMode = g_samplingModeDict['timeInterval']
                samplingTime = optMenu_time.getVal()
                g_samplingDistance = 0 #reset sampling distance apabila mmode sampling time aktif
                menu.menuIndex = g_menuLayer['menu_mode']
            else:
                optMenu_time.dispMenu()
            optMenu_time.poll_prevMenuButton(menu_mode, 1) #jangan dipindah
        
         ##################### MENU PARAMETER INTERVAL JARAK ######################
        elif menu.menuIndex == g_menuLayer['optMenu_dist']:
            #polling push button
            optMenu_dist.poll_increaseVal()
            optMenu_dist.poll_decreaseVal()
            #dibawah ini adalah program untuk save data sampling time yang sudah diset user
            if optMenu_dist.poll_saveData(menu_mode)==True:
                lcd.clear()
                g_samplingMode = g_samplingModeDict['distInterval']
                g_samplingDistance = optMenu_dist.getVal()
                samplingTime = 0 #reset sampling time apabila mode sampling distance aktif
                menu.menuIndex = g_menuLayer['menu_mode']
            else:
                optMenu_dist.dispMenu()
            optMenu_dist.poll_prevMenuButton(menu_mode, 1) #jangan dipindah
        
         ##################### MENU CEK PEMBACAAN SENSOR ######################
        elif menu.menuIndex == g_menuLayer['menu_GPSInfo']: 
            #polling push button
            if menu_GPSInfo.poll_prevMenuButton(menu_start, 0)==True:
                lcd.clear()
            menu_GPSInfo.poll_nextButton()
            menu_GPSInfo.poll_prevButton()
            try:
                sData = sReceivedPosition.readline()
                sData = sData.decode("latin-1").strip()
            except TypeError:
                print("error parsing gps")
                
            DbtDepth, addr = sock.recvfrom(4096)
            DbtDepth = str(DbtDepth).strip()
            for sLine in DbtDepth.splitlines():
                try:
                    sRawData = sLine.split(",")
                    if sRawData[0] == "b'$SDDBT":
                        WaterDepth = float(sRawData[3])
                except TypeError:
                    print("error parsing depth")
                    
            if sData.find("GGA")>0:
                GpggaParseResult = pynmea2.parse(sData)
                #submenu 'coordinate' untuk menampilkan data latitude dan longitude
                if menu_GPSInfo.submenuIndex == g_submenu_GPSInfo['coordinate']:
                    lcd.set_cursor(0,0)
                    lcd.message(f"lat: {GpggaParseResult.latitude}")
                    lcd.set_cursor(0,1)
                    lcd.message(f"long: {GpggaParseResult.longitude}")
                #submenu 'time_and_speed' untuk menampilkan data time utc dan speed over ground
                elif menu_GPSInfo.submenuIndex == g_submenu_GPSInfo['time_and_speed']:
                    lcd.set_cursor(0,0)
                    lcd.message(f"utc: {GpggaParseResult.timestamp}")
                    lcd.set_cursor(0,1)
                    lcd.message(f"depth: {WaterDepth} m") 
            
         
         ##################### MENU START DATA LOGGER######################
        elif menu.menuIndex == g_menuLayer['menu_startLogger']:       
            global g_startLoggingflag
            global g_startSamplingTimeflag      
            global g_TCPDepthConnect
            
            while g_TCPDepthConnect == False: #menunggu koneksi tcp
                try:
                    sock.bind(("", 10110))
                    g_TCPDepthConnect = True
                    print("Successful Connection")
                except:
                    print("Connection Failed")

            g_LoggerIndicator.on()

            if g_samplingMode == g_samplingModeDict['timeInterval']:
                if startThreadflag == False:

                    #setting up flag
                    g_startSamplingTimeflag = True
                    g_startSamplingDistflag = False
                    g_startGetDepthflag = True

                    #starting thread
                    thread1 = Thread(name = "Depth Reader", target=fnGetDepth, args=(GpggaBuffer, DptBuffer, lock))
                    thread2 = Thread(name = "Time Sampling", target=fnReadTime, args=(GpggaBuffer, lock, samplingTime))
                    thread1.start()
                    thread2.start()

                    startThreadflag = True
                
            elif g_samplingMode == g_samplingModeDict['distInterval']:
                if startThreadflag == False:

                    #setting up flag
                    g_startSamplingTimeflag = False
                    g_startSamplingDistflag = True
                    g_startGetDepthflag = True

                    #starting thread
                    thread1 = Thread(name="Depth Reader", target=fnGetDepth, args=(GpggaBuffer, DptBuffer, lock))
                    thread2 = Thread(name="Distance Sampling", target=fnReadDistance, args=(GpggaBuffer, lock))
                    thread1.start()
                    thread2.start()

                    startThreadflag = True
            
            while startThreadflag == True:
                
                if menu_startLogger.poll_prevMenuButton(menu_start, 0)==True:#untuk menghentikan proses data
                    g_startSamplingDistflag = False
                    g_startSamplingTimeflag = False
                    g_startGetDepthflag = False
                    startThreadflag = False

                    #wait until thread finished
                    thread1.join()
                    thread2.join()

                    #emptying queue after usage
                    if not GpggaBuffer.empty():
                        with GpggaBuffer.mutex:
                            GpggaBuffer.queue.clear()
                    
                    if not DptBuffer.empty():
                        with DptBuffer.mutex:
                            DptBuffer.queue.clear()

                    lcd.clear()
                    print("thread end")
                    g_LoggerIndicator.off()
                    g_LoggingIndicator.off()

if __name__=='__main__':
    main()
