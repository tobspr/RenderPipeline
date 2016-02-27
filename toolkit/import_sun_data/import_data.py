

import urllib2
import sys

# You can get this data from http://sunpath.azurewebsites.net/
values = {
        "year": 2016,
        "month": 7,
        "day": 21,
        "latitude": 50.778228759765625,
        "longitude": 6.088640213012695,
        "height": 167
    }

values["end_day"] = values["day"]

API = "http://www.nrel.gov/midc/apps/spa.pl?syear={year}&smonth={month}&sday={day}&eyear={year}&emonth={month}&eday={end_day}&step=15&stepunit=1&latitude={latitude}&longitude={longitude}&timezone=%2B1&elev={height}&press=1013&temp=20&dut1=0.0&deltat=64.797&azmrot=180&slope=0&refract=0.5667&field=2&field=35&field=36&field=38&zip=0"

url = API.format(**values)

print("Querying api ..")
handle = urllib2.urlopen(url)
data = handle.read()
handle.close()

# Extract data
print("Extracting data ..")
lines = data.replace("\r", "").split("\n")[1:]

hour, minutes = 0, 0

data_points_azimuth = []
data_points_altitude = []

for line in lines:
    if not line:
        break
    date, time, azim_angle, declination, ascension, elevation = line.split(",")

    # print(date,"/",hour, minutes, azim_angle, elevation)

    float_azim = (float(azim_angle) + 180.0) / 360.0
    float_elev = (float(elevation) / 60.0) * 0.5 + 0.5

    float_time = (minutes + hour * 60.0) / (24 * 60.0)

    data_points_azimuth.append((float_time, float_azim))
    data_points_altitude.append((float_time, float_elev))

    minutes += 15
    if minutes == 60:
        hour += 1
        minutes = 0


# Load render pipeline api
sys.path.insert(0, "../../")
from rpcore.pluginbase.manager import PluginManager
from rpcore.mount_manager import MountManager

mount_mgr = MountManager(None)
mount_mgr.mount()

plugin_mgr = PluginManager(None)
plugin_mgr.load()


print("Saving ..")
plugin_mgr.day_settings["scattering"]["sun_azimuth"].curves[0].control_points = data_points_azimuth
plugin_mgr.day_settings["scattering"]["sun_altitude"].curves[0].control_points = data_points_altitude

plugin_mgr.save_daytime_overrides("$$config/daytime.yaml")

print("Done!")
