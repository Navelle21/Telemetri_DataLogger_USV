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

#LCD pin setup
lcd_rs = 4
lcd_en = 17
lcd_d4 = 18
lcd_d5 = 22
lcd_d6 = 27
lcd_d7 = 23

#lcd rows and columns pin setup
lcd_columns = 16
lcd_rows = 2

#LCD initialization
lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7,lcd_columns, lcd_rows)

#Push Button Initialization
button_right=Button(5)
button_left=Button(6)
button_ok=Button(25)
button_back=Button(24)

#logger sampling time parameter
samplingTime=0

#sampling mode, 0=time interval, 1=distance interval
samplingMode=0 

#LED12 akan menyala ketika sistem mulai mengambil data dan logging ke SD Card
LoggerIndicator=LED(12)

#class untuk membuat menu
# @ PERHATIAN :
#   class ini menggunakan beberapa fungsi dari library gpiozero dan library AdafruitLCD
# variable Objek :
#   1. subMenu 1, 2, 3, 4 (str): nama subMenu yang akan ditampilkan pada objek menu yang dibuat
#   2. page (int): jumlah halaman dari menu/jumlah subMenu
#   3. maxPage (int): nilai page paling besar
#   4. minPage (int): nilai page paling kecil
#   5. right_button : button untuk pindah ke submenu berikutnya
#   6. left_button : button untuk pindah ke submenu sebelumnya
#   7. ok_button : button untuk pindah ke menu berikutnya
#   8. back_button : button untuk kembali ke menu sebelumnya
class menu:
    
    objectCounter = 0 #variable untuk menentukan jumlah objek yang dibuat
    # menuIndex adalah variable untuk menentukan index dari menu, 
    # contoh : menu_start adalah objek yang dibuat dari class menu, dan menuIndex dari menu_start adalah 1 
    menuIndex = 0 

    def __init__(self, subMenu1='', subMenu2='', subMenu3='', subMenu4=''
    , page=0, maxPage=4, minPage=0, right_button=0, left_button=0, ok_button=0, back_button=0):
        #Inisialisasi submenu
        self.subMenu1=subMenu1
        self.subMenu2=subMenu2
        self.subMenu3=subMenu3
        self.subMenu4=subMenu4

        #inisialisasi push button
        self.right_button=right_button
        self.left_button=left_button
        self.ok_button=ok_button
        self.back_button=back_button

        #inisialisasi index submenu dan menu
        self.submenuIndex=0
        self.page=page

        #inisialisasi jumlah halaman
        self.maxPage=maxPage-1
        self.minPage=minPage
    
    #@brief fungsi untuk berpindah ke subMenu berikutnya
    #@param : pointer objek (self)
    #@retval : tidak ada
    def poll_nextButton(self):
        if self.right_button.is_pressed:
            lcd.clear()
            if(self.page>=self.maxPage):
                self.page=self.maxPage
            else:
                self.page+=1
                sleep(.2)
    
    #@brief fungsi untuk kembali ke subMenu sebelumnya
    #@param : pointer objek (self)
    #@retval : tidak ada
    def poll_prevButton(self):
        if self.left_button.is_pressed:
            lcd.clear()
            if(self.page<=self.minPage):
                self.page=self.minPage
            else:
                self.page-=1
                sleep(.2)
    
    #@brief fungsi untuk berpindah ke subMenu selanjutnya
    #@param : pointer objek (self)
    #@retval : tidak ada
    def poll_nextMenuButton(self):
        if self.ok_button.is_pressed:
            #index submenu:
            self.submenuIndex=self.page+1
            lcd.clear() 
            sleep(.2)
    
    #@brief fungsi untuk berpindah menu ke index tertentu
    #@param : nama menu, index menu
    #@retval : bool status apakah program berhasil atau tidak (program sukses : True, program gagal : False)
    def poll_prevMenuButton(self, previous_menu, prev_menuIndex):
        previous_menu.submenuIndex=0
        if self.back_button.is_pressed:
            lcd.clear()
            menu.menuIndex=prev_menuIndex
            sleep(.2)
            return True

    #@brief fungsi style1 yang akan ditampilkan di LCD, misal menu1 memiliki format LCD dispMenu
    #@param : objek pointer (self)
    #@retval : tidak ada
    def dispMenu(self):
        self.menuList = [self.subMenu1, self.subMenu2, self.subMenu3, self.subMenu4]
        for index, menu in enumerate(self.menuList):
            if index==self.page:
                self.menuLabel=self.menuList[index]
                
        lcd.set_cursor(0,0)
        lcd.message(str(self.page+1))
        lcd.set_cursor(2,0)
        lcd.message(self.menuLabel)
        if self.page==self.maxPage:
            lcd.set_cursor(0,1)
            lcd.message('<<')
        elif self.page==self.minPage:
            lcd.set_cursor(14,1)
            lcd.message('>>')
        else:
            lcd.set_cursor(0,1)
            lcd.message('<<')
            lcd.set_cursor(14,1)
            lcd.message('>>')

#class optionMenu adalah class uji coba, yang nantinya akan dihapus (salah)
class optionMenu(menu):
    objectCounter = 0
    def __init__(self, subMenu1='', subMenu2='', subMenu3='', subMenu4=''
    , page=0, maxPage=4, minPage=0, right_button=0, left_button=0, ok_button=0, back_button=0, 
    maxValue=0, units='', value=0):
        super(optionMenu, self).__init__(subMenu1, subMenu2, subMenu3, subMenu4
        , page, maxPage, minPage, right_button, left_button, ok_button, back_button)
        self.units=units
        self.maxValue=maxValue
        self.value=value
        self.InitialVal=self.value
    
    def poll_increaseVal(self):
        if self.right_button.is_pressed:
            if self.value<self.maxValue:
                self.value+=1
                sleep(.2)
            elif self.value>=self.maxValue:
                self.value=self.value
    
    def poll_decreaseVal(self):
        if self.left_button.is_pressed:
            if self.value>0:
                self.value-=1
                sleep(.2)
            elif self.value<=0:
                self.value=self.value

    def poll_saveData(self, previous_menu):
        if self.ok_button.is_pressed:
            previous_menu.submenuIndex=0
            lcd.clear()
            lcd.set_cursor(4,0)
            lcd.message("saving")
            for i in range(3):
                lcd.message(".")
                sleep(.3)
            self.InitialVal=self.value
            return True
            
    def poll_prevMenuButton(self, previous_menu, prev_menuIndex):
        previous_menu.submenuIndex=0
        if self.back_button.is_pressed:
            lcd.clear()
            self.value=self.InitialVal
            menu.menuIndex=prev_menuIndex
            sleep(.2)

    def getVal(self):
        return self.value

    def dispMenu(self):
        lcd.set_cursor(len(self.subMenu1)+4,0)
        lcd.message(str(self.value))
        lcd.set_cursor(len(self.subMenu1)+5,0)
        lcd.message(self.units)
        lcd.set_cursor(0,1)
        lcd.message("save")
        lcd.set_cursor(10,1)
        lcd.message("cancel")
#*************************************************************

#Tampilan LCD pada startup program
def IntroLCD():
    lcd.set_cursor(7,0)
    lcd.message("USV")
    lcd.set_cursor(3,1)
    lcd.message("Data Logger")
    sleep(2)
    lcd.clear()
    sleep(1)

#deklarasi objek menu
menu_start = menu(subMenu1='Start Logger', subMenu2='Sampling Mode', subMenu3='GPS Info',
             right_button=button_right, left_button=button_left, ok_button=button_ok, back_button=button_back, maxPage=3)

menu_mode = menu(subMenu1='Time', subMenu2='Distance', right_button=button_right, left_button=button_left,
            ok_button=button_ok, back_button=button_back, maxPage=2)

menu_GPSInfo = menu(right_button=button_right, left_button=button_left, ok_button=button_ok, back_button=button_back, maxPage=2)

menu_startLogger = menu(right_button=button_right, left_button=button_left, ok_button=button_ok, back_button=button_back, maxPage=1)

optMenu_time = optionMenu(subMenu1='Time', units='s', value=0, maxValue=5, right_button=button_right, left_button=button_left,
            ok_button=button_ok, back_button=button_back)

#GPS serialPort
serialPort = serial.Serial("/dev/ttyS0", baudrate = 4800, timeout = 0.5)

#   DaftarMenu : 
#   1. menuIndex 0 : menu_start
#      @submenuIndex menu_start : 
#      submenuIndex 1 : StartLogger
#      submenuIndex 2 : Sampling Mode
#      submenuIndex 3 : GPS Info
#
#   2. menuIndex 4 : menu_startLogger/StartLogger (submenu 1 dari menu_start no 1)
#      @submenuIndex menu_startLogger : belum ada, hanya menampilkan data lat, long gps
#       
#   3. menunIdex 1 : menu_mode/Sampling Mode (submenu 2 dari menu_start no 1)
#      @submenuIndex menu_mode :
#      submenuIndex 0 : Time (subMenu untuk setting parameter sampling time)
#      submenuIndex 1 : Distance (subMenu untuk setting parameter sampling distance)
#   
#   4. menuIndex 3 : menu_GPSInfo/GPS Infor (submenu 3 dari menu_start no 1)
#      @submenu : sedang dirapihkan
#
#   5. menuIndex 2 : optMenu_time (submenu 0 dari menu_mode/Sampling Mode)
#      @submenuIndex optMenu_time : sedang dirapihkan

 
def main(): #thread 1

    global samplingMode, LoggerIndicator, samplingTime #untuk sementara dibuat variable global
    
    IntroLCD()
    t0=time() #variable untuk track timer (sampling)
    
    while True:
        #@menuIndex0: menu_start
        if menu.menuIndex==0: 
            menu_start.poll_prevButton()
            menu_start.poll_nextButton()
            menu_start.poll_nextMenuButton()
            menu_start.dispMenu()
            #@submenuIndex 2 : Sampling Mode
            if menu_start.submenuIndex==2: 
                lcd.clear()
                menu.menuIndex=1 #menuIndex1 : menu_mode/Sampling Mode
            else:
                #@brief jika mode Sampling berdasarkan waktu, 
                #       maka akan tampil keterangan 'Time' dibawah tampilan subMenu
                #       Jika mode Sampling berdasarkan jarak, 
                #       maka akan tampil keterangan 'Distance' dibawah tampilan subMenu
                if menu_start.page==1 and samplingMode==0: 
                    lcd.set_cursor(2,1)
                    lcd.message('Time')
                elif menu_start.page==1 and samplingMode==1:
                    lcd.set_cursor(2,1)
                    lcd.message('Distance')
            #submenuIndex 3 : GPS Info
            if menu_start.submenuIndex==3:
                lcd.clear()
                menu.menuIndex=3 #menuIndex 3 : menu_GPSInfo
            #submenuIndex 1 : StartLogger
            if menu_start.submenuIndex==1:
                lcd.clear()
                menu.menuIndex=4 #menuIndex 4 : menu_StartLogger
        #menuIndex 1 : SamplingMode
        elif menu.menuIndex==1:    
            menu_mode.poll_prevButton()
            menu_mode.poll_nextButton()
            menu_mode.poll_nextMenuButton()
            menu_mode.poll_prevMenuButton(menu_start, 0)
            #submenuIndex 1 : sampling mode berdasarkan waktu (Time)
            if menu_mode.submenuIndex==1: 
                lcd.clear()
                menu.menuIndex=2 #menuIndex 2 : setting waktu sampling (sampling time)
            #subemnuIndex 2 : sampling mode berdasarkan jarak (Distance)
            elif menu_mode.submenuIndex==2: 
                lcd.message("empty")    #belum diisi
            menu_mode.dispMenu()
       
       #menuIndex 2 : opsi sampling time (masih dalam proses dirapihkan)
        elif menu.menuIndex==2:  
            optMenu_time.poll_increaseVal()
            optMenu_time.poll_decreaseVal()
            #@brief dibawah ini adalah program untuk save data sampling time yang sudah diset user
            if optMenu_time.poll_saveData(menu_mode)==True:
                lcd.clear()
                samplingMode=0
                samplingTime=optMenu_time.getVal()
                menu.menuIndex=1 #menuIndex 1 : Sampling Mode
            else:
                optMenu_time.dispMenu()
            optMenu_time.poll_prevMenuButton(menu_mode, 1)
        
        #menuIndex 3 : menu_GPSInfor/GPS Info (masih dalam proses dirapihkan)
        elif menu.menuIndex==3: 
            gps_raw = serialPort.readline().decode('latin-1')
            #@brief dibawah ini adalah program untuk parsing data GPS NMEA dengan format data 'RMC'
            if gps_raw.find('RMC') > 0:
                gps_parse = pynmea2.parse(gps_raw)
                menu_GPSInfo.poll_nextButton()
                menu_GPSInfo.poll_prevButton()
                if menu_GPSInfo.poll_prevMenuButton(menu_start, 0)==True:
                    lcd.clear()
                else:
                    if menu_GPSInfo.page==0:
                        lcd.set_cursor(0,0)
                        lcd.message("lat: {}".format(gps_parse.latitude))
                        lcd.set_cursor(0,1)
                        lcd.message("long: {}".format(gps_parse.longitude))
                    elif menu_GPSInfo.page==1:
                        lcd.set_cursor(0,0)
                        lcd.message("utc: {}".format(gps_parse.timestamp))
                        lcd.set_cursor(0,1)
                        lcd.message("speed: {} knots".format(gps_parse.spd_over_grnd))           
        
        #menuIndex 4 : menu_StartLogger/Start Logger (rencana ditambah proses kalman filter untuk memperbaiki data GPS yang kurang stabil)
        elif menu.menuIndex==4: 
            #@brief program untuk set timezone
            LoggerIndicator.on()
            tz = pytz.timezone("Asia/Jakarta")
            today = datetime.datetime.now(tz = pytz.utc)
            gps_raw = serialPort.readline().decode('latin-1')
            #@brief program untuk parsing data GPS NMEA format 'RMC'
            if gps_raw.find('RMC') > 0:
                gps_parse = pynmea2.parse(gps_raw)
                #@brief program untuk memberhentikan proses logging jika pushbutton ditekan
                if menu_startLogger.poll_prevMenuButton(menu_start, 0)==True:
                    lcd.clear()
                    LoggerIndicator.off()
                else:
                    lcd.clear()
                    lcd.message('lat: {} \n'.format(gps_parse.latitude))
                    lcd.message('long: {} \n'.format(gps_parse.longitude))
                    #@brief program untuk polling timer() jika sudah sekian detik maka logging data ke SD Card
                    if time()-t0>samplingTime:
                        with open('gps_logger.csv', 'a+', newline = '') as tracker:
                            csv_writer = csv.writer(tracker, delimiter = '|')
                            csv_writer.writerow(gps_raw)
                        t0=time()
            print(samplingTime)
            

if __name__=='__main__':
    main()