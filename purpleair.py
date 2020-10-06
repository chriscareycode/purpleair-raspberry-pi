#!/usr/bin/env python

# CONFIGURE THIS
# Open up PurpleAir in a web browser. Then open up developer tools -> Network -> XHR
# Click on a single station near you.
# You should see requests being made to a URL that looks like: https://www.purpleair.com/json?show=12345
# Enter the number here:
purpleair_station = "12345"

from random import randint
from time import sleep
from threading import Thread
import json
import datetime as dt

try:
	from urllib.request import Request, HTTPError, URLError, urlopen  # Python 3
except ImportError:
	from urllib2 import Request, HTTPError, URLError, urlopen  # Python 2
import json

# Import Blink(1) USB light
try:
	from blink1.blink1 import Blink1
	blink1_detected = True
	print("blink(1) detected")
except ImportError:
	blink1_detected = False
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

unicorn.brightness(0.5)
width, height = unicorn.get_shape()

# Configure the Blink(1)
if blink1_detected:
	b1 = Blink1()

# store history of numbers we have
history = []
history_max_len = width * height

fetch_every_seconds = 300

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
		
	data = json.load(response)

	#print data
	pm25_string = data["results"][0]["PM2_5Value"]
	print "Got PM2_5Value value: " + pm25_string
	# convert string to float and return function
	return float(pm25_string)


						
# just a note that purpleair api is returning pm25_raw, not US AQI
# we need to figure out the algo to convert the raw to that since that is the number most people refer to
def pm25_to_rgb(pm25_float):
	if pm25_float < 9.0:
		# green
		r = 0
		g = 255
		b = 0
	elif pm25_float < 16:
		# yellow / green
		r = 192
		g = 255
		b = 0
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
		yrange = range(height);

	if unicornhd_detected:
		yrange = range(height - 1, -1, -1);

	for y in yrange:
		for x in range(width):

			# if we have an item in history for this position
			if counter < len(history):

				# pull the data out of the history
				pm25_float_from_history = history[counter]
				rgb_dict = pm25_to_rgb(pm25_float_from_history);
		
				# set the pixel color to the purpleair color
				unicorn.set_pixel(x, y, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])

				counter = counter + 1

	# change unicorn brightness based on time of day
	hour = dt.datetime.now().hour
	#print("hour is " + str(hour))
	if (hour >= 22 or hour < 8):
		if unicornhd_detected:
			unicorn.brightness(0.1)
		else:
			unicorn.brightness(0.3)
	else:
		unicorn.brightness(0.5)

	# flush the changes out to the unicorn hat
	unicorn.show()


def main_loop():
	global fetch_every_seconds
	global blink1_detected
  
	pm25_float_previous = 0


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

			# convert the value to rgb
			rgb_dict = pm25_to_rgb(pm25_float);

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

			# save purpleair reading to an array
			#history.append(pm25_float)
			history.insert(0, pm25_float)

			# if the array has filled up, then trim one off the front
			if len(history) > history_max_len:
				#history.pop(0)
				del history[-1]

			# save history to file (we should only do this every 5m)
			save_history_to_file()


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

