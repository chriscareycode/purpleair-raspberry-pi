# purpleair-raspberry-pi
Display PurpleAir color on a Raspberry Pi with Unicorn Hat and blink(1) light

![Purple Raspberry Pi](https://chriscarey.com/blog/wp-content/uploads/2020/09/purple-pi.png)

## Introduction
I have a Raspberry Pi 2B and a Raspberry Pi 3 each with these lights.

This script currently requires both a Unicorn Hat, and blink(1) light to be present to work.

In the future, I will add some options so the attached hardware used for the lights can be a bit more configurable and modular.

## Hardware to buy

A Raspberry Pi

Unicorn Hat https://shop.pimoroni.com/products/unicorn-hat

blink(1) USB Light https://blink1.thingm.com/

## Install the software for the Unicorn Hat and blink(1) lights

Software for Unicorn Hat
https://learn.pimoroni.com/tutorial/unicorn-hat/getting-started-with-unicorn-hat

Software for Blink(1) USB light
http://blink1.thingm.com/libraries/ (Python)

## How to run the script

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

