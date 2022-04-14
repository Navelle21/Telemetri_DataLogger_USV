#******************************************************************************
# * @file           : loggerUI.py
# * @brief          : API for USV Data Logger Interface
# ******************************************************************************

import Adafruit_CharLCD as LCD
from gpiozero import Button, LED
from time import sleep, time

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
                self.submenuIndex=self.maxPage
            else:
                self.page+=1
                self.submenuIndex=self.page
                sleep(.2)
    
    #@brief fungsi untuk kembali ke subMenu sebelumnya
    #@param : pointer objek (self)
    #@retval : tidak ada
    def poll_prevButton(self):
        if self.left_button.is_pressed:
            lcd.clear()
            if(self.page<=self.minPage):
                self.page=self.minPage
                self.submenuIndex=self.minPage
            else:
                self.page-=1
                self.submenuIndex=self.page
                sleep(.2)
    
    #@brief fungsi untuk berpindah ke subMenu selanjutnya
    #@param : pointer objek (self)
    #@retval : tidak ada
    def poll_nextMenuButton(self):
        if self.ok_button.is_pressed:
            lcd.clear() 
            sleep(.2)
            return True
    
    #@brief fungsi untuk berpindah menu ke index tertentu
    #@param : nama menu, index menu
    #@retval : bool status apakah program berhasil atau tidak (program sukses : True, program gagal : False)
    def poll_prevMenuButton(self, previous_menu, prev_menuIndex):
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

#class optionMenu adalah class Inheritance dari class Menu untuk menu Sammpling Time           
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
        self.currVal=self.value
    
    #@brief fungsi dibawah ini adalah untuk menambah value ketika push button ditekan
    #@param : objek pointer (self)
    #@retval : tidak ada
    def poll_increaseVal(self): 
        if self.right_button.is_pressed:
            if self.value<self.maxValue:
                self.value+=1
                sleep(.2)
            elif self.value>=self.maxValue:
                self.value=self.value
    
      
    #@brief fungsi dibawah ini adalah untuk mengurangi value ketika push button ditekan
    #@param : objek pointer (self)
    #@retval : tidak ada
    def poll_decreaseVal(self):
        if self.left_button.is_pressed:
            if self.value>0:
                self.value-=1
                sleep(.2)
            elif self.value<=0:
                self.value=self.value

    #@brief fungsi dibawah ini adalah untuk menyimpan nilai value yang diubah dan kembali ke menu sebelumnya ketika push button ditekan
    #@param : objek menu sebelumnya
    #@retval : bool TRUE atau FALSE
    def poll_saveData(self, previous_menu):
        if self.ok_button.is_pressed:
            #previous_menu.submenuIndex=0
            lcd.clear()
            lcd.set_cursor(4,0)
            lcd.message("saving")
            for i in range(3):
                lcd.message(".")
                sleep(.3)
            self.currVal=self.value
            return True
        
    #@brief fungsi dibawah ini adalah untuk menyimpan nilai value yang diubah dan kembali ke menu sebelumnya ketika push button ditekan
    #@param : objek menu sebelumnya, menu index sebelumnya
    #@retval : tidak ada
    def poll_prevMenuButton(self, previous_menu, prev_menuIndex):
        #previous_menu.submenuIndex=0
        if self.back_button.is_pressed:
            lcd.clear()
            self.value=self.currVal
            menu.menuIndex=prev_menuIndex
            sleep(.2)
            
    #getter variable value
    def getVal(self):
        return self.currVal

    #tampilan lcd
    def dispMenu(self):
        lcd.set_cursor(len(self.subMenu1)+4,0)
        lcd.message(str(self.value))
        lcd.set_cursor(len(self.subMenu1)+6,0)
        lcd.message(self.units)
        lcd.set_cursor(0,1)
        lcd.message("save")
        lcd.set_cursor(10,1)
        lcd.message("cancel")






