import serial
import time
import struct
import re  # regular expressions used to parse led positions from file
import array
import os

#this class is used to map leds to pixels in the bitmap buffer.
class PixelMapper(object):
	def __init__(self,x_positions,y_positions):
		self.x_positions=x_positions
		self.y_positions=y_positions
	# pick the colors from the defined led-positions and put them in an array...
	def get_colors_from_bitmap(self,bitmap):
		#define a clamping function for convenient limiting of positions
		def clamp(n, minn, maxn): return max(min(maxn, n), minn)
		n_leds=len(self.x_positions)
		output= bytearray(n_leds)
		outpos=0 #position in the output buffer
		for i in range(n_leds):
			output[outpos:outpos+3]=bitmap.get_at(clamp(self.x_positions[i],0,bitmap.width-1),clamp(self.y_positions[i],0,bitmap.height-1))
			outpos+=3
		return output
	# scale the coordinates (can be useful to fit them to a given buffer size)
	def scale(self,x_scale,y_scale):
		for i in range(len(self.x_positions)):
			self.x_positions[i]*=x_scale
			self.y_positions[i]*=y_scale
	# add an offset to the coordinates (can be useful to fit them to a given buffer size)
	def add_offset(self,x_offset,y_offset):
		for i in range(len(self.x_positions)):
			self.x_positions[i]+=x_offset
			self.y_positions[i]+=y_offset
			
	def create_from_file(filename):
		if (not os.path.exists(filename)):
			print ('Led position definition file not found!')
			return
		file=open(filename,'r')	#open position file
		content=file.read()		#put the content into a string
		
		#now we extract the part of the file that interests us: the 'positions' array.
		#find the definition of the 'positions' array
		start_matcher=re.compile(r'Point\s*positions\s*\[.*\]\s=\s\{') 
		match_result=start_matcher.search(content)
		if(match_result== None):
			print ('couldn\'t find beginning of points array in file!')
			return
		content=content[match_result.end():] #strip all the uninteresting part at the beginning...
		#find the closing bracket of the array definition
		end_matcher=re.compile(r'\}') 
		match_result=end_matcher.search(content)
		if(match_result== None):
			print ('couldn\'t find end of points array in file!')
			return
		content=content[:match_result.start()] #strip everything that comes after the bracket
		
		#at this point, we should have the content of the array in a string.
		
		# now we split it at all comma's
		string_parts=content.split(',')
		
		#and finally put the content into the right lists...
		isX=True # the first part is an x-coordinate
		x_pos=array.array('f',[])
		y_pos=array.array('f',[])
		for part in string_parts:
			#if we cannot convert it, we just skip it...
			try: 
				if (isX):
					x_pos.append(int(part))
				else:
					y_pos.append(int(part))
				isX= not isX
			except ValueError: 
				pass
		if(len(x_pos)!=len(y_pos)):
			print ('LED coordinate list contains contains an odd number of numbers!')
			return
		return PixelMapper(x_pos,y_pos)


#this class manages communication with the wearable led suit
class LedInterface(object):
	TIMEOUT=0 # used as a return value of send_bitmap
	TRANSMITTED=1
	UNKNOWN_REQUEST=2
	def __init__(self,port=0,timeout=0.01):
		# we expect the serial port to be configured to 115200 baud - we need it as fast as possible...
		self.serial_port=serial.Serial(port,115200,timeout=timeout) #change this to match your envirmonent!
	#send raw bitmap-data to the wearable. this only makes sense if your wearable interprets the data to fit its layout, which is usually not the case.
	def send_bitmap(self,bitmap,timeout=0.01):
		return self.send_bytearray(bitmap.convert_to_RGB().pixels) #data is sent as reordered RGB to fit the data structure in the mcu
	
	#send an array containing color information to the wearable. Use s PixelMapper to get arrays that fit to your layout.
	def send_bytearray(self,send_data,timeout=0.01):
		#before we send anything, we wait for a handshake so that no data will be lost
		self.serial_port.flushInput() # throw away all old data
		read_data=self.serial_port.read(1) # we expect to get the letter 't' from the MCU
		if(len(read_data)<1): return LedInterface.TIMEOUT #if we didn't get a send permission, we just don't do anything
		if(read_data[0]!= 116): return LedInterface.UNKNOWN_REQUEST #if we didn't get a send permission, we just don't do anything
		#now that the mcu seems to be ready to receive data, we transmitt our command and pixel data
		# we have 10ms time to send the command byte, after that, the inter-char timeout is a mellow 100ms
		self.serial_port.write(b'p') # ASCII code 112  'p' stands for pixeldata
		self.serial_port.write(struct.pack('<I',len(send_data))) # length of the pixelarray follows as a little endian unsigned long
		self.serial_port.write(send_data) #data is sent as reordered RGB to fit the data structure in the mcu
		print(self.serial_port.read(2000))
		return LedInterface.TRANSMITTED
		
		
		

		
		
		
		
		
		
		
		

