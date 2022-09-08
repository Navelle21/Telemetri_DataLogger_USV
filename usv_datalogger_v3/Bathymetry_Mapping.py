import numpy as np
from numpy import genfromtxt
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib  import cm
from scipy.interpolate import griddata

data_dir = ''
file_name = 'batsaragam.csv'
bath_data = genfromtxt(file_name, delimiter=',')

print(type(bath_data))
print(bath_data.ndim)
print(bath_data.shape)

lon = bath_data[:,1]
lat = bath_data[:,2]
depth = bath_data[:,3]

fig = plt.figure()
fx = fig.add_subplot(231)
plt.title("Bathy Measurement Locations")
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.plot(lon, lat, '.')
dL = 0.0005
plt.xlim([lon.min()-dL, lon.max()+dL])
plt.ylim([lat.min()-dL, lat.max()+dL])



ax = fig.add_subplot(232)
ax.plot(lon, lat, '.')
ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
plt.xlabel("Longitue")
plt.ylabel("Latitude")

dp = fig.add_subplot(233)
sc = dp.scatter(lon, lat, s=20, c=depth, marker='o', cmap = cm.jet);
dp.yaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
dp.xaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.colorbar(sc)

UTMx = lon
UTMy = lat

xRange = UTMx.max() - UTMx.min()
yRange = UTMy.max() - UTMy.min()

print("xRange : %f" %xRange)
print("yRange : %f" %yRange)

dX = 2
X = np.arange(UTMx.min(), UTMx.max(), dX)
Y = np.arange(UTMy.min(), UTMy.max(), dX)
print(X)
print(Y)
grid_x, grid_y = np.meshgrid(X, Y, sparse=False, indexing='xy')
zi = griddata((UTMx, UTMy), depth, (grid_x, grid_y), method='linear')

# print(grid_x.shape)

contp = fig.add_subplot(234)
contp.yaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
contp.xaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
cp = plt.scatter(grid_x, grid_y, c=zi, cmap = cm.jet)
#p = plt.contourf(grid_x, grid_y, zi)
# plt.xlim([grid_x.min(), grid_x.max()])
# plt.ylim([grid_y.min(), grid_y.max()])
#plt.scatter(lon, lat)
plt.colorbar(cp)


lonRange = int((lon.max()-lon.min())/2.0) + 2
latRange = int((lat.max()-lat.min())/2.0) + 2



lon_spc = np.linspace(lon.min(), lon.max(), 40)
lat_spc = np.linspace(lat.min(), lat.max(), 40)
lon_grid, lat_grid = np.meshgrid(lon_spc, lat_spc, sparse=False, indexing='xy')
zL = griddata((lon, lat), depth, (lon_grid, lat_grid), method='linear')
cont2 = fig.add_subplot(235)
cp2 = plt.contourf(lon_grid, lat_grid, zL, cmap = cm.jet)
#cp2 = plt.scatter(lon_grid, lat_grid, c=zL, cmap=cm.jet);
#cp2 = plt.scatter(lon_grid, lat_grid)
#plt.scatter(lon, lat)
#cp2 = plt.scatter(lon_grid, lat_grid, c=zL, cmap=cm.jet)
cont2.yaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
cont2.xaxis.set_major_formatter(mtick.FormatStrFormatter('%d'))
plt.xlabel("Longitude")
plt.ylabel("Latitude")
plt.colorbar(cp2)
plt.show()

# UTMx = lon
# UTMy = lat

# print(UTMx.max() - UTMx.min())

# dX = 20
# X = np.arange(UTMx.min(), UTMx.max(), dX)
# Y = np.arange(UTMy.min(), UTMy.max(), dX)
# grid_x, grid_y = np.meshgrid(X, Y, sparse=False, indexing='xy')


# from scipy.interpolate import griddata
# zi = griddata((UTMx, UTMy), depth, (grid_x, grid_y),method='linear')

# print(grid_x.shape)
# print(zi.shape)

# lon_spc = np.linspace(lon.min(), lon.max(), 30)
# lat_spc = np.linspace(lat.min(), lat.max(), 30)
# lat_grid, lon_grid = np.meshgrid(lat_spc, lon_spc, sparse=False, indexing='xy')
# zL = griddata((lat, lon), depth, (lat_grid, lon_grid),method='cubic')
# #fig = plt.figure(figsize=(10,6))
# #ax = fig.add_subplot(141)
# cp = plt.contourf(lat_grid, lon_grid, zL, cmap = cm.jet)
# #ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%.4f'))
# #ax.xaxis.set_major_formatter(mtick.FormatStrFormatter('%.4f'))
# plt.xlabel("Easting") 
# plt.ylabel("Northing") 
# plt.title("Hasil Pemetaan Batimetri")
# plt.colorbar(cp)
# plt.show()
