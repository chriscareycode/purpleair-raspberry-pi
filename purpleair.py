#!/usr/bin/env python

# CONFIGURE THIS
# Open up PurpleAir in a web browser. Then open up developer tools -> Network -> XHR
# Click on a single station near you.
# You should see requests being made to a URL that looks like: https://www.purpleair.com/json?show=12345
# Enter the number here:
purpleair_station = "12345"
enable_blink1 = True
enable_influxdb = False

from random import randint
from time import sleep
from threading import Thread
import json
import datetime as dt
import socket
import math
if enable_influxdb:
	# https://influxdb-python.readthedocs.io/en/latest/include-readme.html
	from influxdb import InfluxDBClient
	client = InfluxDBClient('10.0.0.11', 8086, None, None, 'custom_home')

try:
	from urllib.request import Request, HTTPError, URLError, urlopen  # Python 3
except ImportError:
	from urllib2 import Request, HTTPError, URLError, urlopen  # Python 2
import json

# Import Blink(1) USB light
blink1_detected = False
if enable_blink1:
	try:
		from blink1.blink1 import Blink1
		blink1_detected = True
		print("blink(1) detected")
	except ImportError:
		print("No blink(1) detected")

# Import Unicorn Hat
try:
	import unicornhat as unicorn
	unicorn_detected = True
	print("Unicorn Hat detected")
except ImportError:
	unicorn_detected = False
	print("No Unicorn Hat detected")

try:
	import unicornhathd as unicorn
	unicornhd_detected = True
	print("Unicorn Hat HD detected")
except ImportError:
	unicornhd_detected = False
	print("No Unicorn Hat HD detected")

# Configure the Unicorn Hat
#unicorn.set_layout(unicorn.AUTO)

if unicorn_detected:
	unicorn.rotation(90)

if unicornhd_detected:
	unicorn.rotation(0)

if unicorn_detected or unicornhd_detected:
  unicorn.brightness(0.4)
  width, height = unicorn.get_shape()
else:
  width = 8
  height = 8

# Configure the Blink(1)
if blink1_detected:
	b1 = Blink1()

# store history of numbers we have
history = []
history_max_len = width * height

fetch_every_seconds = 300

# thanks to Mike Bostock https://observablehq.com/@mbostock/pm25-to-aqi
def lerp(ylo, yhi, xlo, xhi, x):
  return ((x - xlo) / (xhi - xlo)) * (yhi - ylo) + ylo

def pm25_aqi(pm25):
  c = math.floor(10 * pm25) / 10
  if c < 0:
    a = 0
  elif c < 12.1:
    a = lerp(  0,  50,   0.0,  12.0, c)
  elif c < 35.5:
    a = lerp( 51, 100,  12.1,  35.4, c)
  elif c < 55.5:
    a = lerp(101, 150,  35.5,  55.4, c)
  elif c < 150.5:
    a = lerp(151, 200,  55.5, 150.4, c)
  elif c < 250.5:
    a = lerp(201, 300, 150.5, 250.4, c)
  elif c < 350.5:
    a = lerp(301, 400, 250.5, 350.4, c)
  elif c < 500.5:
    a = lerp(401, 500, 350.5, 500.4, c)
  else:
    a = 500

  # a = c < 0 ? 0 # values below 0 are considered beyond AQI
  #   : c <  12.1 ? lerp(  0,  50,   0.0,  12.0, c)
  #   : c <  35.5 ? lerp( 51, 100,  12.1,  35.4, c)
  #   : c <  55.5 ? lerp(101, 150,  35.5,  55.4, c)
  #   : c < 150.5 ? lerp(151, 200,  55.5, 150.4, c)
  #   : c < 250.5 ? lerp(201, 300, 150.5, 250.4, c)
  #   : c < 350.5 ? lerp(301, 400, 250.5, 350.4, c)
  #   : c < 500.5 ? lerp(401, 500, 350.5, 500.4, c)
  #   : 500 # values above 500 are considered beyond AQI

  return round(a)

# def aqi_pm25(aqi):
#   a = math.round(aqi)
#   c = a < 0 ? 0 # values below 0 are considered beyond AQI
#     : a <=  50 ? lerp(  0.0,  12.0,   0,  50, a)
#     : a <= 100 ? lerp( 12.1,  35.4,  51, 100, a)
#     : a <= 150 ? lerp( 35.5,  55.4, 101, 150, a)
#     : a <= 200 ? lerp( 55.5, 150.4, 151, 200, a)
#     : a <= 300 ? lerp(150.5, 250.4, 201, 300, a)
#     : a <= 400 ? lerp(250.5, 350.4, 301, 400, a)
#     : a <= 500 ? lerp(350.5, 500.4, 401, 500, a)
#     : 500 # values above 500 are considered beyond AQI
#   return math.floor(10 * c) / 10
# }

#print "input: 25 output: " + str(pm25_aqi(25))
#exit(0)

def fetch_purpleair():

	url = "https://www.purpleair.com/json?show=" + purpleair_station

	# technique with headers
	req = Request(url)
	req.add_header('accept', 'application/json, text/javascript, */*; q=0.01')
  

	try:
		response = urlopen(req)
	except HTTPError, err:
		if err.code == 404:
			print "Page not found!"
		elif err.code == 403:
			print "Access denied!"
		elif err.code == 429:
			print "Too Many Requests"
		elif err.code == 500:
			print "Internal Server Error"
		else:
			print "Something happened! Error code", err.code
		return None
	except URLError, err:
		print "Some other error happened:", err.reason
		return None
	except BadStatusLine:
		print "Error BadStatusLine"
		return None
		
	data = json.load(response)

	#print data
	pm25_string = data["results"][0]["PM2_5Value"]
	print "Got PM25 value: " + pm25_string
	# convert string to float and return function
	return float(pm25_string)


def aqi_to_rgb(aqi_float):
	if aqi_float < 50.0:
		# green
		r = 0
		g = 255
		b = 0
	#elif aqi_float < 75:
		# yellow / green
		#r = 192
		#g = 255
		#b = 0
	elif aqi_float < 100:
		# yellow
		r = 255
		g = 255
		b = 0
	elif aqi_float < 150:
		# orange
		r = 255
		g = 141
		b = 24
	elif aqi_float < 175:
		# dark orange
		r = 236
		g = 87
		b = 43
	elif aqi_float < 200:
		# red
		r = 235
		g = 71
		b = 40
	elif aqi_float < 300:
		# purple
		r = 142
		g = 7
		b = 138
	else:
		# maroon (TODO)
		r = 142
		g = 7
		b = 138

	return {"r": r, "g": g, "b": b}

# just a note that purpleair api is returning pm25_raw, not US AQI
# we need to figure out the algo to convert the raw to that since that is the number most people refer to
def pm25_to_rgb(pm25_float):
	if pm25_float < 9.0:
		# green
		r = 0
		g = 255
		b = 0
	#elif pm25_float < 16:
		# yellow / green
		#r = 192
		#g = 255
		#b = 0
	elif pm25_float < 22:
		# yellow
		r = 255
		g = 255
		b = 0
	elif pm25_float < 48:
		# orange
		r = 255
		g = 141
		b = 24
	elif pm25_float < 52:
		# dark orange
		r = 236
		g = 87
		b = 43
	elif pm25_float < 95:
		# red
		r = 235
		g = 71
		b = 40
	else:
		# purple
		r = 142
		g = 7
		b = 138

	return {"r": r, "g": g, "b": b}




def draw_history_to_unicorn():
	global history

	counter = 0

	if unicorn_detected:
		xrange = range(width)
		yrange = range(height)

	if unicornhd_detected:
		#xrange = range(width)
		#yrange = range(height - 1, -1, -1)
		xrange = range(8)
		yrange = range(8 - 1, -1, -1)
		#yrange = range(8)

	for y in yrange:
		for x in xrange:

			# if we have an item in history for this position
			if counter < len(history):

				# pull the data out of the history
				aqi_float_from_history = history[counter]
				rgb_dict = aqi_to_rgb(aqi_float_from_history)
		
				#print("x is " + str(x) + " and y is " + str(y))

				# set the pixel color to the purpleair color
				if unicorn_detected:
					unicorn.set_pixel(x, y, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])

				if unicornhd_detected:
					unicorn.set_pixel(x*2, y*2, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])
					unicorn.set_pixel(x*2+1, y*2, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])
					unicorn.set_pixel(x*2, y*2+1, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])
					unicorn.set_pixel(x*2+1, y*2+1, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])

				counter = counter + 1

	# change unicorn brightness based on time of day
	#hour = dt.datetime.now().hour
	##print("hour is " + str(hour))
	#if (hour >= 22 or hour < 8):
	#	if unicornhd_detected:
	#		unicorn.brightness(0.1)
	#	else:
	#		unicorn.brightness(0.4)
	#else:
	#	unicorn.brightness(0.5)

	# flush the changes out to the unicorn hat
	unicorn.show()


def main_loop():
	global fetch_every_seconds
	global blink1_detected

	pm25_float_previous = 0
	aqi_float_previous = 0


	while True:
		
		hour = dt.datetime.now().hour
		#print("hour is " + str(hour))
		
		# fetch data from purpleair. Return the pm25 raw data in pm25_float
		pm25_float = fetch_purpleair()

		if pm25_float is None:
			# if we had an error fetching from purpleiar, then show the previous value
			# but in that routine we will change the dot color so we know it's stale data
			
			print("got bad data")
		else:
			# we got good data from purpleair
			aqi_float = pm25_aqi(pm25_float)
			print("Got AQI " + str(aqi_float))
			# convert the value to rgb
			#rgb_dict = pm25_to_rgb(pm25_float)
			rgb_dict = aqi_to_rgb(aqi_float)

			# change brightness based on time of day
			


			# set blink(1) USB color (changes based on time of day)
			if blink1_detected:
				if (hour >= 22 or hour < 8):
					if blink1_detected:
						b1.off()
				else:
					if blink1_detected:
						b1.fade_to_rgb(1000, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])
				

			# save the previous purpleair value in a variable
			pm25_float_previous = pm25_float
			aqi_float_previous = aqi_float

			# save purpleair reading to an array
			#history.append(pm25_float)
			#history.insert(0, pm25_float)
			history.insert(0, aqi_float)

			# if the array has filled up, then trim one off the front
			if len(history) > history_max_len:
				#history.pop(0)
				del history[-1]

			# save history to file (we should only do this every 5m)
			save_history_to_file()

			if enable_influxdb:
				# write pm25 metric to InfluxDB
				influx_payload = [{
					"measurement": "air_quality",
					"fields": {"value": pm25_float},
					"tags": {"host": socket.gethostname()},
					"time": dt.datetime.utcnow().replace(microsecond=0).isoformat()
				}]
				print(influx_payload)
				try:
					client.write_points(influx_payload)
					print("Wrote to InfluxDB")
				except Exception as e:
					print("Connection Error InfluxDB")
					print(e)

				# write aqi metric to InfluxDB
				influx_payload = [{
					"measurement": "air_quality_aqi",
					"fields": {"value": aqi_float},
					"tags": {"host": socket.gethostname()},
					"time": dt.datetime.utcnow().replace(microsecond=0).isoformat()
				}]
				print(influx_payload)
				try:
					client.write_points(influx_payload)
					print("Wrote to InfluxDB")
				except Exception as e:
					print("Connection Error InfluxDB")
					print(e)


		draw_history_to_unicorn()

		sleep(fetch_every_seconds)

# the white dot will loop around the pi, when it reaches the end is about the time purpleair will fetch

def white_dot_loop():
	global height
	global width
	global fetch_every_seconds

	sleep_time = fetch_every_seconds / float(height * width)
	print("fetch_every_seconds is " + str(fetch_every_seconds))
	print("height is " + str(height))
	print("width is " + str(width))
	print("height * width is " + str(height * width))
	print("sleep_time is " + str(sleep_time))
	while True:

		if unicorn_detected:
			yrange = range(height);

		if unicornhd_detected:
			yrange = range(height - 1, -1, -1);

		for y in yrange:
			for x in range(width):

				#we can run into timing issue when we save the pixel it can change. so lets flush the history out periodically to fix
				# this is a weak fix to my multi threaded bug with the white dot. lets turn this off and fix the issue another way
				#if x == 7:
				#	draw_history_to_unicorn()

				#print("white dot loop")
				saved_pixel = unicorn.get_pixel(x, y)
				#print(pixel)
				unicorn.set_pixel(x, y, 200, 200, 200)
				unicorn.show()
				sleep(sleep_time)
				unicorn.set_pixel(x, y, saved_pixel[0], saved_pixel[1], saved_pixel[2])
				unicorn.show()

def white_dot_knight_rider():
	while True:

		y = 7 # last row
		for y in range(height):
			for x in range(width):

				#we can run into timing issue when we save the pixel it can change. so lets flush the history out periodically to fix
				if x == 7:
					draw_history_to_unicorn()

				#print("white dot loop")
				saved_pixel = unicorn.get_pixel(x, y)
				#print(pixel)
				unicorn.set_pixel(x, y, 200, 200, 200)
				unicorn.show()
				sleep(4.6875)
				unicorn.set_pixel(x, y, saved_pixel[0], saved_pixel[1], saved_pixel[2])
				unicorn.show()

def save_history_to_file():
	global history

	with open('purpleair-history.txt', 'w') as filehandle:
		json.dump(history, filehandle)

def load_history_from_file():
	global history
	try:
		with open('purpleair-history.txt', 'r') as filehandle:
			history = json.load(filehandle)
	except:
		print "Could not find history file to load"

if __name__ == "__main__":

	# program starts here

	# check if the purpleair station was properly configured
	if purpleair_station == "12345":
		print "You need to edit purpleair.py and set the purpleair_station to a station near you"
		exit(0)

	load_history_from_file()

	thread1 = Thread(target=main_loop)
	thread1.daemon = True
	thread1.start()

	thread2 = Thread(target=white_dot_loop)
	thread2.daemon = True
	thread2.start()

	while True:
		sleep(1)

