# purpleair-raspberry-pi

Display PurpleAir color on a Raspberry Pi with Unicorn Hat and blink(1) light

## Introduction

With all the fires in California, I was checking ![PurpleAir](https://purpleair.com) multiple times per day to track what the air is like outside – waiting for a moment when the AQI improves so we can open some windows or take a walk. It seemed like a good idea to use some of these Raspberry Pi computers to always show the air quality. At least, while the fires are still active.

I have a bunch of Raspberry Pi boards handy, and two with the Pimoroni Unicorn Hat 64 RGB light array on them. This would work perfectly as a display for current air quality conditions.

In addition I have a few of the Blink(1) USB lights. This will add even more color.

*Unicorn Hat* is a 8x8 RGB LED matrix that sits on top of the Raspberry Pi

*blink(1)* is a USB device with two RGB LED lights (one on each side)

![Purple Raspberry Pi](https://chriscarey.com/blog/wp-content/uploads/2020/09/purple-pi.png)


## Hardware to buy

A Raspberry Pi

Unicorn Hat https://shop.pimoroni.com/products/unicorn-hat

blink(1) USB Light https://blink1.thingm.com/

On these Pis I used the C4Labs Zebra Case https://www.amazon.com/gp/product/B00M6G9YBM/ - It fits around the Unicorn Hat pretty well.

(These links are just to the product pages, you can probably find these items at many online retailers)

## Install the software for the Unicorn Hat and blink(1) lights

Software for Unicorn Hat
https://learn.pimoroni.com/tutorial/unicorn-hat/getting-started-with-unicorn-hat

Software for Blink(1) USB light
http://blink1.thingm.com/libraries/ (Python)

## How to run the script

This script currently requires both a Unicorn Hat, and blink(1) light to be present to work.

The example scripts for the Unicorn Hat and the blink(1) light execute as root in order to be able to access the hardware.
There are some ways to get around this and run as non-root and I'd like to investigate this more in the future to tighten this down.
For now though, the way to run this script is:

```bash
sudo ./purpleair.py
```

### Getting the script to run when the Pi boots up:

The way I'm setting this up right now is to use "screen" to launch this in on boot

```bash
apt install screen
```

Edit /etc/rc.local

At the bottom of rc.local, ABOVE exit 0, add:

```bash
# start purpleair in screen
su - pi -c "/usr/bin/screen -dmS purpleair sudo /home/pi/purpleair.py"
```

Make sure `screen` is installed

```bash
apt install screen
```

Reboot your Raspberry Pi and see if the script starts on it's own.

This will create a new "screen" session named "purpleair" with the purpleair script running inside of it

### TODO

* Detect which hardware is installed and react appropriately (Support if only Unicorn Hat is detected, or only blink(1) is detected, or both)
* Make adding new hardware types easy
* Decouple the timing mechanism for how often to hit PurpleAir API from the Unicorn Hat display. Decouple the white pixel from the timing as well.
* Instead of specific "steps" for color - green, yellow, orange, red, dark red, purple - add support for smooth gradient between these colors.


