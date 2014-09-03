from freetypescroll import *
#contains all the logic (and data) we use to decide what to do with incoming messages

# a list with all known effect commands. Messages containing those will be forwarded to the Wearable 'as is'
effectCommands=[
'#flash',
'#fade',
'#glitter',
'#fill',
'#move',
'#rainbow'
]


#checks if a message contains a command. returns true or false
def containsCommand(message):
	for command in effectCommands:
		if(command in message): return True
	return False
class ColorMapper:
	def __init__(self):
		self.primaryColor=[255,255,255]
		self.secondaryColor=[0,0,0]
		self.colorCommands={
		'#green':[0,255,0],
		'#cyan':[0,255,255],
		'#blue':[0,0,255],
		'#mauve':[224,176,255],
		'#pink':[255,0,255],
		'#red':[255,0,0],
		'#orange':[255,128,0],
		'#yellow':[255,255,0],
		'#white':[255,255,255],
		'#black':[0,0,0]
		}
	def parse_colors(self,message):
		words= message.split(' ')
		n_colors=0
		for word in words:
			if(word in self.colorCommands):
				if(n_colors==0):
					self.primaryColor=self.colorCommands[word]
					n_colors=1
				else:
					self.secondaryColor=self.primaryColor
					self.primaryColor=self.colorCommands[word]
	def convert_to_colors(self,mono_bitmap):
		rgb_bytes=bytearray(len(mono_bitmap.pixels)*3)
		dstindex=0
		for mono in mono_bitmap.pixels:
			rgb_bytes[dstindex]=int(float(mono)*float(self.primaryColor[0])/255.0+float(255-mono)*float(self.secondaryColor[0])/255.0)
			rgb_bytes[dstindex+1]=int(float(mono)*float(self.primaryColor[1])/255.0+float(255-mono)*float(self.secondaryColor[1])/255.0)
			rgb_bytes[dstindex+2]=int(float(mono)*float(self.primaryColor[2])/255.0+float(255-mono)*float(self.secondaryColor[2])/255.0)
			dstindex+=3
		return ColorBitmap(mono_bitmap.width, mono_bitmap.height,rgb_bytes)