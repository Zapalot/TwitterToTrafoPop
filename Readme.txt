---Introduction
This documentation is under develeopment. It will be ready on 31.08.2014..
Receiving Twitter messages, rendering and display already works.
Invoking effects is not implemented yet, it will come by fusing the effects from the Twiolio-Project with "minimalReceiver"

---How To Install:
Wearable side:
1. Upload th Arduino sketch "minimalReceiver"

PC/Raspberry side:
1. Install python, if you haven't yet.
2. Install the freetype and twitter and pySerial modules:
Open a command prompt and type:
--
pip install pyserial
---
git clone https://github.com/rougier/freetype-py.git
cd freetype-py
python setup.py install
pip install twitter

3. Windows users: Put Freetype.dll to the right place:
Copy the freetype.dll into your windows/Systen32 and/or windows/SysWOW64 directories

4. Adjust LED-Positions to those of your own wearable
Replace the 'positions.h' with the LED-Position definition of you own wearable.
You might want to have a look into 'scrollToLeds.py' and to adjust the coordinate-scaling, fontsize and other details to match your wearable.


6. You are ready to go!

---How To Run:
open a command prompt and run:
python scrollToLeds.py
If you run the app for the first time or you have changed your credentials, you will have to go through the "oAuthDance" to auhtenticate the program to twitter. A Browser window will open for that.

tweets containing @trafopoptest will be scrolled on the LEDs