import serial
import time
import struct
import re  # regular expressions used to parse led positions from file
import array
import os



#this class manages communication with the wearable led suit
class LedInterface(object):
	TIMEOUT=0 # used as a return value of send_bitmap
	READY=1
	TRANSMITTED=2
	UNKNOWN_REQUEST=3
	def __init__(self,port=0,timeout=0.03):
		# we expect the serial port to be configured to 115200 baud - we need it as fast as possible...
		self.serial_port=serial.Serial(port,115200,timeout=timeout) #change this to match your envirmonent!
		
	#wait until we get permission to send data to the wearable. this helf to avoid congestion on the serial interface.
	def wait_for_handshake(self,timeout=0.3):
		self.serial_port.timeout=timeout
		#print("waiting for 't'")	
		#before we send anything, we wait for a handshake so that no data will be lost
		self.serial_port.flushInput() # throw away all old data
		read_data=self.serial_port.read(1) # we expect to get the letter 't' from the MCU
		if(len(read_data)<1): return LedInterface.TIMEOUT #if we didn't get a send permission, we just don't do anything
		if(read_data[0]!= 116 and read_data[0]!='t' ): return LedInterface.UNKNOWN_REQUEST #if we didn't get a send permission, we just don't do anything
		return LedInterface.READY # if we have arrived here, everything seems to be fine
	def send_keep_alive	(self,timeout=0.3):
		# wait for data request:
		print ("alive....??")
		handshake_result=self.wait_for_handshake(timeout)
		if(handshake_result!=LedInterface.READY): return handshake_result
		self.serial_port.write(b'a') # 'a' stands for 'alive'
		print ("...yeees")
	# send a command string to the wearable:
	def send_command(self,command,timeout=0.3):
		# wait for data request:
		handshake_result=self.wait_for_handshake(timeout)
		if(handshake_result!=LedInterface.READY): return handshake_result
		self.serial_port.write(b'c') # 'c' stands for command
		self.serial_port.write(command.encode(encoding='ascii',errors='ignore')) # transmitt message, skip all non ASCII-characters
		return LedInterface.TRANSMITTED
		
	#send an array containing color information to the wearable. Use s PixelMapper to get arrays that fit to your layout.
	def send_bytearray(self,send_data,timeout=0.3):
		print ("sending"+str(len(send_data))+"bytes of data")
		# wait for data request:
		handshake_result=self.wait_for_handshake(timeout)
		if(handshake_result!=LedInterface.READY): return handshake_result
		
		#now that the mcu seems to be ready to receive data, we transmitt our command and pixel data
		# we have 10ms time to send the command byte, after that, the inter-char timeout is a mellow 100ms
		self.serial_port.write(b'p') # ASCII code 112  'p' stands for pixeldata
		self.serial_port.write(struct.pack('<I',len(send_data))) # length of the pixelarray follows as a little endian unsigned long
		self.serial_port.write(send_data) #data is sent as reordered RGB to fit the data structure in the mcu
		self.serial_port.flush()
		#self.serial_port.timeout=0.01
		#print(self.serial_port.read(2000))
		return LedInterface.TRANSMITTED
	#send raw bitmap-data to the wearable. this only makes sense if your wearable interprets the data to fit its layout, which is usually not the case.
	def send_bitmap(self,bitmap,timeout=0.3):
		return self.send_bytearray(bitmap.convert_to_RGB().pixels,timeout) #data is sent as reordered RGB to fit the data structure in the mcu
		
		

		
		
		
		
		
		
		
		

