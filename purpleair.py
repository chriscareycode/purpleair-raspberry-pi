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

try:
	from urllib.request import Request, HTTPError, URLError, urlopen  # Python 3
except ImportError:
	from urllib2 import Request, HTTPError, URLError, urlopen  # Python 2
import json

# Import Blink(1) USB light
from blink1.blink1 import Blink1

# Import Unicorn Hat
import unicornhat as unicorn

# Configure the Unicorn Hat
unicorn.set_layout(unicorn.AUTO)
unicorn.rotation(90)
unicorn.brightness(0.5)
width, height = unicorn.get_shape()

# Configure the Blink(1)
b1 = Blink1()

# store history of numbers we have
history = []
history_max_len = 64

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

# this routine takes 5m to run due to the sleep()
def set_color(pm25_float, is_error):

	print str(pm25_float)

	rgb_dict = pm25_to_rgb(pm25_float);
	r = rgb_dict["r"]
	g = rgb_dict["g"]
	b = rgb_dict["b"]
	print r, g, b

	# set blink(1) USB color
	b1.fade_to_rgb(1000, r, g, b)

	# set unicorn hat to the color
	# This looks a bit more complicated than it needs to be since I decided to have the color on the
	# hat change pixel by pixel gradually over time. In addition, I wanted a pixel on the display to slowly change
	# so that we can see the script is still running. I chose to use a white pixel that moves around the hat
	# and when that white pixel reaches the bottom right corner, it will fetch from purpleair again.
	# This routine is what is "slowing down" the fetching so its not happening all the time.
	# By having a sleep(5) here, we are sleeping 5 seconds between each pixel change.
	# With 64 pixels, we are sleeping 64 * 5 seconds before fetch_purpleair runs again

	for y in range(height):
		for x in range(width):

			# set the color to the white dot (or blue if error)
			if is_error:
				# show blue dot if error (will be displaying old data)
				unicorn.set_pixel(x, y, 0, 0, 255)
			else:
				# show white dot if no error
				unicorn.set_pixel(x, y, 200, 200, 200)

			# flush the changes out to the unicorn hat
			unicorn.show()
			# sleep 5 seconds
			sleep(5)
			# set the pixel color to the purpleair color
			unicorn.set_pixel(x,y,r,g,b)
			# flush the changes out to the unicorn hat
			unicorn.show()
						
# just a note that purpleair api is returning pm25_raw, not US AQI
# we need to figure out the algo to convert the raw to that since that is the number most people refer to
def pm25_to_rgb(pm25_float):
	if pm25_float < 9.0:
		# green
		r = 0
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

	for y in range(height):
		for x in range(width):

			# if we have an item in history for this position
			if counter < len(history):

				# pull the data out of the history
				pm25_float_from_history = history[counter]
				rgb_dict = pm25_to_rgb(pm25_float_from_history);
		
				# set the pixel color to the purpleair color
				unicorn.set_pixel(x, y, rgb_dict["r"], rgb_dict["g"], rgb_dict["b"])

				counter = counter + 1

	# flush the changes out to the unicorn hat
	unicorn.show()


def main_loop():
	global fetch_every_seconds

	pm25_float_previous = 0

	while True:
		# fetch data from purpleair. Return the pm25 raw data in pm25_float
		pm25_float = fetch_purpleair()

		if pm25_float is None:
			# if we had an error fetching from purpleiar, then show the previous value
			# but in that routine we will change the dot color so we know it's stale data
			#set_color(pm25_float_previous, True)
			print("got bad data")
		else:
			# we got good data from purpleair

			# convert the value to rgb
			rgb_dict = pm25_to_rgb(pm25_float);

			# set blink(1) USB color
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

	  	# draw the purple air data
	  	#set_color(pm25_float, False)

		draw_history_to_unicorn()

		sleep(fetch_every_seconds)

# the white dot will loop around the pi, when it reaches the end is about the time purpleair will fetch

def white_dot_loop():
	sleep_time = fetch_every_seconds % height * width
	while True:

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

