#!/usr/bin/env python3
from jplephem import Ephemeris
from skyfield.api import load
from skyfield.almanac import moon_phase

eph = load('de421.bsp')
earth, moon, sun = eph['earth'], eph['moon'], eph['sun']
ts = load.timescale()
t = ts.now()

t=ts.utc(2022,1,2,18,33) #new moon sunlat - moonlat = 0
t=ts.utc(2022,5,5,12,25,57) #beltane cross quarter sun latitude = 45 deg
_,sunlat,_=earth.at(t).observe(sun).apparent().ecliptic_latlon('date')
_,moonlat,_=earth.at(t).observe(moon).apparent().ecliptic_latlon('date')
print(str(t))
print('sunlat=',sunlat)
print('moonlat=',moonlat)

sunra,_,_=earth.at(t).observe(sun).apparent().radec()
print('sunra=',sunra)
