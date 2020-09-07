# purpleair-raspberry-pi
Display PurpleAir color on a Raspberry Pi with Unicorn Hat and blink(1) light

This script currently requires both a Unicorn Hat, and blink(1) light to be present to work.

In the future, I will add some options so it works with one or the other, or both.

The example scripts for the Unicorn Hat and the blink(1) light execute as root in order to be able to access the hardware.
There are some ways to get around this and run as non-root and I'd like to investigate this more in the future to tighten this down.
For now though, the way to run this script is:

sudo ./purpleair.py

Getting the script to run when the Pi boots up:

The way I'm setting this up right now is to use "screen" to launch this in on boot

apt install screen

Edit /etc/rc.local

At the bottom of rc.local, ABOVE exit 0, add:

# purpleair
su - pi -c "/usr/bin/screen -dmS purpleair sudo /home/pi/purpleair.py"

This will create a new "screen" session named "purpleair" with the purpleair script running inside of it

