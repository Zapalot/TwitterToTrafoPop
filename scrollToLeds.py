########################################
# Setup connection to the led-wearable.
# The pySerial module is used for this purpose.
# Default Baudrate is 115200
########################################
from ledinterface import *
ledcom=LedInterface(port="COM41") # adjust the serial-port to your system

########################################
# Load LED-positions from file and create an object that will map pixel positions to led indices
########################################
pixel_mapper= PixelMapper.create_from_file("positions.h")
#tweak led-postions to fit into a pixel-grid. You might have to adjust this to fit your wearable layout!
pixel_mapper.scale(0.5,-0.5) # scale the led coordinates. You can use negative numbers to mirror the output.
pixel_mapper.add_offset(-min(pixel_mapper.x_positions),-min(pixel_mapper.y_positions)) #let the coordiantes begin at (0,0)

########################################
# Setup the font-rendering system.
########################################
from freetypescroll import *
font_size=8 #you can adjust the fontsize to youe wearable here!
font_y_offset=((max(pixel_mapper.y_positions)-min(pixel_mapper.y_positions))-font_size)/2 #center text vertically
textFont = Font('04B_03__.ttf', font_size) # The file containing the font has to be in the same folder as this sketch!
#the 'scroller' draws a moving text... Speed is in 'pixels/second'
# Calculate the size of a drawing surface that fits to our LEDs
bufHeight=(max(pixel_mapper.y_positions)-min(pixel_mapper.y_positions)+1) # make sure we have enough pixels for the whole wearable
bufWidth=(max(pixel_mapper.x_positions)-min(pixel_mapper.y_positions)+1)  # make sure we have enough pixels for the whole wearable
scroller=TextScroller(width=bufWidth,height=bufHeight,x_offset=0,y_offset=font_y_offset,speed=10,font=textFont)

########################################
# Setup twitter connectivity
########################################
import twittersetup #we have put all the details into a separate file. Look here to change credentials.
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
twitter_stream=twittersetup.get_twitter_stream() #twittersetup.py contains all the details..
# Get a python iterator that will stream all tweets matching certain filter criteria to us.
filter_args = dict() # all the parameters of the query are put in this dictionary
filter_args['track'] = '@TrafoPopTest' # 'track' is a Twitter API parameter explained here:https://dev.twitter.com/docs/streaming-apis/parameters#track
tweet_iter = twitter_stream.statuses.filter(**filter_args) # this establishes the connection to twitter

scroller.set_text('Waiting @TrafoPopTest!')

########################################
# receive until the end of days...
########################################
while(1):
	next_filter_match=next(tweet_iter)# get the next tweet that matches our filter criteria
	# Test what kind of message we got (it may be some status report or error message...)
	if next_filter_match is None:
		print("-- None --")
	elif next_filter_match is Timeout:
		print("-- Timeout --")
	elif next_filter_match is HeartbeatTimeout:
		print("-- Heartbeat Timeout --")
	elif next_filter_match is Hangup:
		print("-- Hangup --")
	elif next_filter_match.get('text'):
		print(next_filter_match['text'].encode('utf-8'))
		scroller.set_text(next_filter_match['text']) # set the scroller to the desired text
	else:
		printNicely("-- Some data: " + str(next_filter_match))

	#show the result.
	scroller.scroll_by_time() # let the scroller move the text around as desired
	ledcom.send_bytearray(pixel_mapper.get_colors_from_bitmap(scroller.output_buffer.convert_to_RGB()))
	print(scroller.output_buffer)