import numpy
import pyaudio
import threading
from ledinterface import *

class SwhRecorder:
    """Simple, cross-platform class to record from the microphone."""

    def __init__(self):
        """minimal garb is executed when class is loaded."""
        self.RATE=48100
        self.BUFFERSIZE=2**12 #1024 is a good buffer size
        self.secToRecord=.1
        self.threadsDieNow=False
        self.newAudio=False

    def setup(self):
        """initialize sound card."""
        #TODO - windows detection vs. alsa or something for linux
        #TODO - try/except for sound card selection/initiation

        self.buffersToRecord=int(self.RATE*self.secToRecord/self.BUFFERSIZE)
        if self.buffersToRecord==0: self.buffersToRecord=1
        self.samplesToRecord=int(self.BUFFERSIZE*self.buffersToRecord)
        self.chunksToRecord=int(self.samplesToRecord/self.BUFFERSIZE)
        self.secPerPoint=1.0/self.RATE	

        self.p = pyaudio.PyAudio()
        self.inStream = self.p.open(format=pyaudio.paALSA,channels=1,
            rate=self.RATE,input=True,frames_per_buffer=self.BUFFERSIZE)
        self.xsBuffer=numpy.arange(self.BUFFERSIZE)*self.secPerPoint
        self.xs=numpy.arange(self.chunksToRecord*self.BUFFERSIZE)*self.secPerPoint
        self.audio=numpy.empty((self.chunksToRecord*self.BUFFERSIZE),dtype=numpy.int16)               

    def close(self):
        """cleanly back out and release sound card."""
        self.p.close(self.inStream)

    ### RECORDING AUDIO ###  

    def getAudio(self):
        """get a single buffer size worth of audio."""
        audioString=self.inStream.read(self.BUFFERSIZE)
        return numpy.fromstring(audioString,dtype=numpy.int16)

    def record(self,forever=True):
        """record secToRecord seconds of audio."""
        while True:
            if self.threadsDieNow: break
            for i in range(self.chunksToRecord):
                self.audio[i*self.BUFFERSIZE:(i+1)*self.BUFFERSIZE]=self.getAudio()
            self.newAudio=True
            if forever==False: break

    def continuousStart(self):
        """CALL THIS to start running forever."""
        self.t = threading.Thread(target=self.record)
        self.t.start()

    def fft(self,data=None,trimBy=10,logScale=False,divBy=100):
        if data==None:
            data=self.audio.flatten()
        left,right=numpy.split(numpy.abs(numpy.fft.fft(data)),2)
        ys=numpy.add(left,right[::-1])
        if logScale:
            ys=numpy.multiply(20,numpy.log10(ys))
        xs=numpy.arange(self.BUFFERSIZE/2,dtype=float)
        if trimBy:
            i=int((self.BUFFERSIZE/2)/trimBy)
            ys=ys[:i]
            xs=xs[:i]*self.RATE/self.BUFFERSIZE
        if divBy:
            ys=ys/float(divBy)
        return xs,ys

# modify the jacket LED columns according to the mic input
def visualize(col, n):
  # make it dividable by 3, not to fuckup colors on the LEDs
  n = n * 3
  # cut mic input that is above jacket LED column threshold
  if n > len(col): n = len(col)
  # check if jacket LED column is upside down or not
  if col[1] == 0x10:
    # set jacket LED column height
    col = col[:n] + ( (len(col) - n) * bytearray([0x00]) )
  else:
    # reverse mic input
    n = len(col) - n
    # set jacket LED column height
    col = ( n * bytearray([0x00]) ) + col[n:]
  return col

# define jacket colors
red = bytearray([0x10, 0x00, 0x00])
green = bytearray([0x00, 0x10, 0x00])
blue = bytearray([0x00, 0x00, 0x10])
yellow = bytearray([0x25, 0x15, 0x00])
orange = bytearray([0x40, 0x10, 0x00])
black = bytearray([0x00, 0x00, 0x00])

# define not used LEDs
fuckup3 = bytearray([0x00]*3*3)
fuckup6 = bytearray([0x00]*6*3)
fuckup7 = bytearray([0x00]*7*3)
fuckup13 = bytearray([0x00]*13*3)
front_left = bytearray([0x00]*19*3)
front_right = bytearray([0x00]*19*3)

# define jacket LED columns
col1 = red * 1 + orange * 2 + yellow * 2 + green * 2
col2 = green * 2 + yellow * 2 + orange * 2 + red * 2
col3 = red * 2 + orange * 2 + yellow * 2 + green * 3
col4 = green * 3 + yellow * 3 + orange * 2 + red * 2
col5 = red * 2 + orange * 2 + yellow * 3 + green * 3
col6 = green * 4 + yellow * 3 + orange * 3 + red * 2
col7 = red * 2 + orange * 3 + yellow * 3 + green * 4
col8 = green * 5 + yellow * 3 + orange * 3 + red * 2
col9 = red * 2 + orange * 2 + yellow * 3 + green * 6
col10 = green * 6 + yellow * 3 + orange * 2 + red * 2
col11 = red * 2 + orange * 2 + yellow * 2 + green * 5
col12 = green * 3 + yellow * 2 + orange * 2 + red * 2
col13 = red * 1 + orange * 2 + yellow * 2 + green * 2

# open a connection to the jacket
#ledcom = LedInterface(port="/dev/ttyACM0") # adjust the serial-port to your system (Teensy or Pro Micro on RasPi)
ledcom = LedInterface(port="/dev/ttyUSB0") # adjust the serial-port to your system (Nano on RasPi)

# initiate mic recorder
SR=SwhRecorder()
# setup mic recorder
SR.setup()
# start continues mic recording
SR.continuousStart()

while True:
    # when new audio available
    if SR.newAudio:
	# calculate fft
	xs, ys = SR.fft()
	tum = []
	# the used data indexes
	indexes = [13, 14, 15, 16, 17, 27, 28, 29, 32, 33, 34, 35, 36]
	# scale down the frequency responses for the jacket
	for i in indexes: 
	    tum.append(int(ys[i] / 1000))
	    print int(ys[i] / 1000),
	print ""

	# assemble data to be sent for jacket
	send_data = front_left + visualize(col1, tum[0]) + visualize(col2, tum[1]) + visualize(col3, tum[2]) + fuckup3
	send_data += visualize(col4, tum[3]) + visualize(col5, tum[4]) + fuckup6 + visualize(col6, tum[5]) + visualize(col7, tum[6]) + fuckup7
	send_data += visualize(col8, tum[7]) + visualize(col9, tum[8]) + fuckup13 + visualize(col10, tum[9]) + visualize(col11, tum[10])
	send_data += visualize(col12, tum[11]) + visualize(col13, tum[12]) + front_right

	# send data to the jacket
	ledcom.send_bytearray(send_data)
