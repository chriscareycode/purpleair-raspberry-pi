#!/usr/bin/env python

# CONFIGURE THIS
# Open up PurpleAir in a web browser. Then open up developer tools -> Network -> XHR
# Click on a single station near you.
# You should see requests being made to a URL that looks like: https://www.purpleair.com/json?show=12345
# Enter the number here:
purpleair_station = "12345"

from random import randint
from time import sleep

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

def set_color(pm25_float, is_error):

        print str(pm25_float)

        if pm25_float < 9.0:
                # green
                r = 0
                g = 255
                b = 0
                print "green"
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
                        

if __name__ == "__main__":

        # program starts here

        # check if the purpleair station was properly configured
        if purpleair_station == "12345":
                print "You need to edit purpleair.py and set the purpleair_station to a station near you"
                exit(0)

        pm25_float_previous = 0

        while True:
                # fetch data from purpleair. Return the pm25 raw data in pm25_float
                pm25_float = fetch_purpleair()

                if pm25_float is None:
                        # if we had an error fetching from purpleiar, then show the previous value
                        # but in that routine we will change the dot color so we know it's stale data
                        set_color(pm25_float_previous, True)
                else:
                        # we got good data from purpleair
                        # save the previous purpleair value in a variable
                        pm25_float_previous = pm25_float
                        # show the new purpleair data
                        set_color(pm25_float, False)



