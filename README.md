Sistem USV Data Logger dan Telemetri secara garis besar tersusun atas lima proses, yaitu:
1. Membaca data time utc, latitude, longitude, speed over ground, dari format GPRMC GPS
2. membaca data kedalaman perairan dari format SDDPT echosounder
3. menyimpan data pembacaan ke sd card dalam bentuk csv dengan urutan "time utc, latitude, longitude, speed over ground, water depth"
4. hasil pembacaan data koordinat latitude, longitude dapat dipetakan kedalam bentuk 2 dimensi
5. data pembacaan dapat di kirim melalui jaringan internet (wifi 2.4G/4G "belum ditentukan) dan ditampilkan melalui dashboard menggunakan platform IoT
(Sampling rate pembacaan data dapat ditentukan berdasarkan interval waktu atau interval jarak)

Interaksi User dengan dengan sistem dapat melalui sistem GUI LCD dan monitoring melalui dashboard platform IoT.
LCD GUI 16x2 dapat dikontrol menggunakan 4 buah tombol, yaitu :
1. tombol 1 : untuk fungsi previous submenu
2. tombol 2 : untuk fungsi next submenu
3. tombol 3 : untuk fungsi ok
4. tombol 4 : untuk fungsi back (previous menu)

melalui GUI LCD 16x2, user dapat :
1. menentukan mode sampling data (berdasarkan jarak atau waktu)
2. melihat data pembacaan gps
3. memulai dan menghentikan sistem logging

Program sistem ini ditulis dengan metode multithreading, terbagi atas :
1. thread menampilkan LCD GUI 
2. thread membaca data GPS 
3. thread membaca data echosounder
4. thread logging data ke sd card
5. thread untuk kirim data melalui jaringan internet (IoT)

-sinkronisasi antar thread menggunakan variable boolean sebagai flag
-transfer data antar thread menggunakan struktur data Queue
