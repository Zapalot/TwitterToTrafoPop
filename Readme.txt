----------------------
- StartUp
----------------------
After Installation, type
----
python scrollToLeds.py 

look inside the script for more information - there is a lot of comments inside...
----
into a shell to start the python script

----------------------
-Installation (PC/Raspberry side)
----------------------
------------Arduoino/Teensy Installation
Plug in Arduino or Teensy. Usually it works right out of the box and appears under /dev/ttyUSB0 or /dev/ttyACM0
Else, follow the instructions here:
http://playground.arduino.cc/Linux/All#Permission
---  To add permission to access Nano open a shell and type. 
sudo usermod -a -G dialout pi ///for Arduino Nano
--- For Teensy Install copy udev rule file according to https://www.pjrc.com/teensy/td_download.html
sudo cp RasPi/49-teensy.rules /etc/udev/rules.d/
------
--------------------Python Library Installation
Next we install some libraries:
  - Python Serial Library that manages communication with your Wearable.
  - PythonTwitter Library that manages communication with twitter
  - Python Freetype Library to render fonts
---  Open a shell and type:(using python 2):
sudo pip install pyserial 
sudo pip install twitter  
git clone https://github.com/rougier/freetype-py.git
cd freetype-py
sudo python setup.py install
---
----(or using python 3 instead of python 2):
Install python 3 package manager: (http://stackoverflow.com/questions/10763440/how-to-install-python3-version-of-package-via-pip)
sudo aptitude install python3-setuptools
sudo easy_install3 pip
sudo pip3.2 install pyserial
sudo pip3.2 install twitter
git clone https://github.com/rougier/freetype-py.git
cd freetype-py
sudo python3 setup.py install
---
-----------Autostart on Boot via Init-Script
I took my description from here. a look at the file described here:http://www.pietervanos.net/knowledge/start-python-script-from-init-d/
A (dirty) init script that starts 'scrollToLeds.py' is in Raspi/twitterToTrafoPopStart
---You can use it by typing:
sudo cp Raspi/twitterToTrafoPopStart /etc/init.d/
sudo chmod 755 /etc/init.d/twitterToTrafoPopStart
---
----------------Wireless config:
I read http://www.geeked.info/raspberry-pi-add-multiple-wifi-access-points/
To edit WPA2 Network names and Passwords:
sudo nano /etc/wpa_supplicant.conf

To add a Section for a network:
sudo wpa_passphrase yourSSID yourPassPhrase >> /etc/wpa_supplicant.conf

----------------------
-Installation (Windows)
----------------------
Install Python
Install Python Libraries with the same commands as on a Raspi.
Put Freetype.dll to the right place:
Copy the freetype.dll into your windows/Systen32 and/or windows/SysWOW64 directories

----------------------
-Installation (Wearable side)
----------------------
Take a look at the the 'Receiver+Effects' Program "twitterReceiverWithEffects" for Arduino and Teensy 3.0/1
Adjust Settings like LED Type, LED-Numbers, Maximum Current and Positions
Upload it.

