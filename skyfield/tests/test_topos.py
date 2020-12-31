from assay import assert_raises
from numpy import abs, sqrt

from skyfield import constants
from skyfield.api import Distance, load, wgs84, wms
from skyfield.functions import length_of
from skyfield.positionlib import Apparent, Barycentric
from skyfield.toposlib import ITRSPosition, iers2010

angle = (-15, 15, 35, 45)

def ts():
    yield load.timescale()

def test_raw_itrs_position():
    d = Distance(au=[1, 2, 3])
    p = ITRSPosition(d)
    ts = load.timescale()
    t = ts.utc(2020, 12, 16, 12, 59)
    p.at(t)

def test_velocity():
    # It looks like this is a sweet spot for accuracy: presumably a
    # short enough fraction of a second that the vector does not time to
    # change direction much, but long enough that the direction does not
    # get lost down in the noise.
    factor = 300.0

    ts = load.timescale()
    t = ts.utc(2019, 11, 2, 3, 53, [0, 1.0 / factor])
    jacob = wgs84.latlon(36.7138, -112.2169)
    p = jacob.at(t)
    velocity1 = p.position.km[:,1] - p.position.km[:,0]
    velocity2 = p.velocity.km_per_s[:,0]
    assert length_of(velocity2 - factor * velocity1) < 0.0007

def test_lst():
    ts = load.timescale()
    ts.delta_t_table = [-1e99, 1e99], [69.363285] * 2  # from finals2000A.all
    t = ts.utc(2020, 11, 27, 15, 34)
    top = wgs84.latlon(0.0, 0.0)
    expected = 20.0336663100  # see "authorities/horizons-lst"
    actual = top.lst_hours_at(t)
    difference_mas = (actual - expected) * 3600 * 15 * 1e3
    horizons_ra_offset_mas = 51.25
    difference_mas -= horizons_ra_offset_mas
    assert abs(difference_mas) < 1.0

def test_itrf_vector():
    top = wgs84.latlon(45.0, 0.0, elevation_m=constants.AU_M - constants.ERAD)

    x, y, z = top.itrs_xyz.au
    assert abs(x - sqrt(0.5)) < 2e-7
    assert abs(y - 0.0) < 1e-14
    assert abs(z - sqrt(0.5)) < 2e-7

    ts = load.timescale()
    t = ts.utc(2019, 11, 2, 3, 53)
    x, y, z = top.at(t).itrf_xyz().au
    assert abs(x - sqrt(0.5)) < 1e-4
    assert abs(y - 0.0) < 1e-14
    assert abs(z - sqrt(0.5)) < 1e-4

def test_polar_motion_when_computing_topos_position(ts):
    xp_arcseconds = 11.0
    yp_arcseconds = 22.0
    ts.polar_motion_table = [0.0], [xp_arcseconds], [yp_arcseconds]

    top = iers2010.latlon(wms(42, 21, 24.1), wms(-71, 3, 24.8), 43.0)
    t = ts.utc(2020, 11, 12, 22, 2)

    # "expected" comes from:
    # from novas.compat import ter2cel
    # print(ter2cel(t.whole, t.ut1_fraction, t.delta_t, xp_arcseconds,
    #               yp_arcseconds, top.itrs_position.km, method=1))

    expected = (3146.221313017412, -3525.955228249315, 4269.301880718039)
    assert max(abs(top.at(t).position.km - expected)) < 6e-11

def test_polar_motion_when_computing_altaz_coordinates(ts):
    latitude = 37.3414
    longitude = -121.6429
    elevation = 1283.0
    ra_hours = 5.59
    dec_degrees = -5.45

    xp_arcseconds = 11.0
    yp_arcseconds = 22.0
    ts.polar_motion_table = [0.0], [xp_arcseconds], [yp_arcseconds]

    t = ts.utc(2020, 11, 12, 22, 16)
    top = wgs84.latlon(latitude, longitude, elevation)

    pos = Apparent.from_radec(ra_hours, dec_degrees, epoch=t)
    pos.t = t
    pos.center = top

    alt, az, distance = pos.altaz()

    # To generate the test altitude and azimuth below:
    # from novas.compat import equ2hor, make_on_surface
    # location = make_on_surface(latitude, longitude, elevation, 0, 0)
    # (novas_zd, novas_az), (rar, decr) = equ2hor(
    #     t.ut1, t.delta_t, xp_arcseconds, yp_arcseconds, location,
    #     ra_hours, dec_degrees, 0,
    # )
    # novas_alt = 90.0 - novas_zd

    novas_alt = -58.091982532734704
    novas_az = 1.887311822537328

    assert abs(alt.degrees - novas_alt) < 1.9e-9
    assert abs(az.degrees - novas_az) < 1.3e-7

def test_subpoint_with_wrong_center(ts, angle):
    t = ts.utc(2020, 12, 31)
    p = Barycentric([0,0,0], t=t)
    with assert_raises(ValueError, 'a geographic subpoint can only be'
                       ' calculated for positions measured from 399, the center'
                       ' of the Earth, but this position has center 0'):
        wgs84.subpoint(p)

def test_iers2010_subpoint(ts, angle):
    t = ts.utc(2018, 1, 19, 14, 37, 55)
    # An elevation of 0 is more difficult for the routine's accuracy
    # than a very large elevation.
    top = iers2010.latlon(angle, angle, elevation_m=0.0)
    p = top.at(t)
    b = iers2010.subpoint(p)

    error_degrees = abs(b.latitude.degrees - angle)
    error_mas = 60.0 * 60.0 * 1000.0 * error_degrees
    assert error_mas < 0.1

    error_degrees = abs(b.longitude.degrees - angle)
    error_mas = 60.0 * 60.0 * 1000.0 * error_degrees
    assert error_mas < 0.1

def test_wgs84_subpoint(ts, angle):
    t = ts.utc(2018, 1, 19, 14, 37, 55)
    # An elevation of 0 is more difficult for the routine's accuracy
    # than a very large elevation.
    top = wgs84.latlon(angle, angle, elevation_m=0.0)
    p = top.at(t)
    b = wgs84.subpoint(p)

    error_degrees = abs(b.latitude.degrees - angle)
    error_mas = 60.0 * 60.0 * 1000.0 * error_degrees
    assert error_mas < 0.1

    error_degrees = abs(b.longitude.degrees - angle)
    error_mas = 60.0 * 60.0 * 1000.0 * error_degrees
    assert error_mas < 0.1

def test_deprecated_position_subpoint_method(ts, angle):
    t = ts.utc(2018, 1, 19, 14, 37, 55)
    top = iers2010.latlon(angle, angle, elevation_m=0.0)
    b = top.at(t).subpoint()

    error_degrees = abs(b.latitude.degrees - angle)
    error_mas = 60.0 * 60.0 * 1000.0 * error_degrees
    assert error_mas < 0.1

    error_degrees = abs(b.longitude.degrees - angle)
    error_mas = 60.0 * 60.0 * 1000.0 * error_degrees
    assert error_mas < 0.1
