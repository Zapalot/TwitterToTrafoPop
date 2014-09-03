#####################################
###
# Setup connection to the led-wearable.
# The pySerial module is used for this purpose.
# Default Baudrate is 115200
########################################
import time
from ledinterface import *
ledcom=LedInterface(port="/dev/ttyACM0") # adjust the serial-port to your system (Teensy or Pro Micro on RasPi)
#ledcom=LedInterface(port="/dev/ttyUSB0") # adjust the serial-port to your system (Nano on RasPi)
#ledcom=LedInterface(port="COM3") # adjust the serial-port to your system (My windows machine)
#ledcom=LedInterface(port="COM20") # adjust the serial-port to your system (My windows machine)
#ledcom=LedInterface(port="COM45") # adjust the serial-port to your system (My windows machine)

########################################
# Setup message parsing system
########################################
from messageparsing  import *
colorator = ColorMapper() #this guy will look for color commands and colorize our bitmaps accordingly
scrollText=True #set False after sending an effect command
########################################
# Load LED-positions from file and create an object that will map pixel positions to led indices
########################################
jacket='stripe'
if(jacket=='thomas'):
	pixel_mapper= PixelMapper.create_from_file("positions.h_thomas")
	#tweak led-postions to fit into a pixel-grid. You might have to adjust this to fit your wearable layout!
	pixel_mapper.scale(0.5,-0.5) # scale the led coordinates. You can use negative numbers to mirror the output.
	pixel_mapper.add_offset(-min(pixel_mapper.x_positions),-min(pixel_mapper.y_positions)) #let the coordiantes begin at (0,0)
	font_size=8 #you can adjust the fontsize to youe wearable here!
	font_name='04B_03__.TTF'
	font_y_offset=((max(pixel_mapper.y_positions)-min(pixel_mapper.y_positions))-font_size)/2 #center text vertically
	led_height=(max(pixel_mapper.y_positions)-min(pixel_mapper.y_positions)+1) # make sure we have enough pixels for the whole wearable
	led_width=(max(pixel_mapper.x_positions)-min(pixel_mapper.y_positions)+1)  # make sure we have enough pixels for the whole wearable	
	
if(jacket=='david'):
	pixel_mapper= PixelMapper.create_from_file("positions.h_david")
	#tweak led-postions to fit into a pixel-grid. You might have to adjust this to fit your wearable layout!
	pixel_mapper.scale(25.0/(max(pixel_mapper.x_positions)-min(pixel_mapper.x_positions)),-48.0/(max(pixel_mapper.y_positions)-min(pixel_mapper.y_positions))) # scale the led coordinates. You can use negative numbers to mirror the output.
	pixel_mapper.add_offset(-min(pixel_mapper.x_positions),-min(pixel_mapper.y_positions)) #let the coordiantes begin at (0,0)
	font_size=16	#you can adjust the fontsize to youe wearable here!
	font_name='unibody/Unibody8Pro-Bold.otf'
	font_y_offset=-1 # text should start at top
	led_height=(32) # make sure we have enough pixels for the whole wearable
	led_width=(max(pixel_mapper.x_positions)-min(pixel_mapper.x_positions)+1)  # make sure we have enough pixels for the whole wearable	

if(jacket=='stripe'):
	pixel_mapper= PixelMapper.create_from_file("positions.h_stripe")
	#tweak led-postions to fit into a pixel-grid. You might have to adjust this to fit your wearable layout!
	font_size=8	#you can adjust the fontsize to youe wearable here!
	font_name='unibody/Unibody8Pro-Regular.otf'
	font_y_offset=-2 # text should start at top
	led_height=(max(pixel_mapper.y_positions)-min(pixel_mapper.y_positions)+1) # make sure we have enough pixels for the whole wearable
	led_width=(max(pixel_mapper.x_positions)-min(pixel_mapper.x_positions)+1)  # make sure we have enough pixels for the whole wearable	
########################################
# Setup the font-rendering system.
########################################
from freetypescroll import *
my_font = Font(font_name, font_size) # The file containing the font has to be in the same folder as this sketch!

#the 'scroller' draws a moving text... Speed is in 'pixels/second'
# Calculate the size of a drawing surface that fits to our LEDs
scroll_speed=20#pixels/second
scroll_text='Waiting for Tweets @TrafoPopTest!'

#render text to buffer with all our settings and convert to color
def render_text(text):
	return(time.time(),colorator.convert_to_colors(my_font.render_text(text,height=led_height,y_offset=font_y_offset)))
#get pexel data for a shifting window in the text
if(jacket=='stripe'):
	def get_scrolled_pixel_data(): 
		x_offset=(float(scroll_speed)*float(time.time()-scroll_time))%(scroll_buffer.width+led_width)-led_width
		return pixel_mapper.get_colors_from_grid(scroll_buffer,x_offset=x_offset,led_width=60,led_height=10)
else:
	def get_scrolled_pixel_data(): 
		x_offset=(float(scroll_speed)*float(time.time()-scroll_time))%(scroll_buffer.width+led_width)-led_width
		return pixel_mapper.get_colors_from_bitmap(scroll_buffer,x_offset=x_offset)
	
scroll_time,scroll_buffer=render_text('Waiting for Tweets @TrafoPopTest!') #set an initial text	
def is_scroll_finished():
		return (float(scroll_speed)*float(time.time()-scroll_time))>(scroll_buffer.width+led_width)*2


########################################
# Setup twitter connectivity
########################################
import twittersetup #we have put all the details into a separate file. Look here to change credentials.
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup

########################################
#Moderator support for public places
########################################
moderator_names=['trafopopAutomat','TrafoJacket'] # a List of screen names that are allowed to show messages even if cencorship is enabled
censorship=False

def get_user_name(tweet):
	if(tweet.get('text')):
		if(tweet.get('user')):
			if tweet.get('user').get('screen_name'): return tweet.get('user').get('screen_name')
	return none
def is_from_moderator(tweet):
	if (any(get_user_name(tweet)==s for s in moderator_names)):
		return True
	else:
		return False
	
def get_cencorship_from_message(tweet):
	if (not is_from_moderator(tweet)): return censorship #don't change anything
	print ('Der moderator sagt:')
	if  tweet.get('text').find('schluss jetzt')>0:
		print ('dont feed the trolls!')
		return True
	if tweet.get('text').find('offen fuer alle')>0:
		print ('Viel Spass Kids!')
		return False

########################################
# receive until the end of days... - we've put everything into a try block and a loop to minimize potential for trouble at the show...
########################################
while(1):
	try:
		print ("trying to connect to twitter...")
		#try to establish a connection to twitter.
		
		twitter_stream=twittersetup.get_twitter_stream() #twittersetup.py contains all the details..
		# Get a python iterator that will stream all tweets matching certain filter criteria to us.
		filter_args = dict() # all the parameters of the query are put in this dictionary
		filter_args['track'] = 'TrafoJacket' # 'track' is a Twitter API parameter explained here:https://dev.twitter.com/docs/streaming-apis/parameters#track
		tweet_iter = twitter_stream.statuses.filter(**filter_args) # this establishes the connection to twitter
		print ("twitter connection successful ...")
		scroll_time,scroll_buffer=render_text('Waiting for Tweets with Keyword TrafoJacket!') #set an initial text
		
		scrollText=True #set False after sending an effect command
		#receive until something breaks....
		while(1):
			old_time=time.time()
			next_filter_match=next(tweet_iter)# get the next tweet that matches our filter criteria
			#print ('twitter took:'+str(time.time()-old_time))
			# Test what kind of message we got (it may be some status report or error message...)
			if next_filter_match is None:
				print("-- None --")
			elif next_filter_match is Timeout:
				True
				#print("-- Timeout --")
			elif next_filter_match is HeartbeatTimeout:
				print("-- Heartbeat Timeout --")
				scrollText=True 	# otherwise, it will be displayed as text
				scroll_time,scroll_buffer=render_text("Twitter connection lost...") #set scrolled text
			elif next_filter_match is Hangup:
				print("-- Hangup --")
				scrollText=True 	# otherwise, it will be displayed as text
				scroll_time,scroll_buffer=render_text("Twitter connection lost...") #set scrolled text
			elif next_filter_match.get('text'):
				censorship=get_cencorship_from_message(next_filter_match) # update moderator control
				message_text=next_filter_match['text']# extract message content and convert to plain ascii
				print(message_text.encode(encoding='ascii',errors='ignore') ) #for debug purposes...
				#print all messages as long as cencorship is disabled
				#check if the message contains a command. A list of them is contained in 'messageparsing.py'
				if (containsCommand(message_text)):
					scrollText=False 	#In that case, it will be forwarded directly to the wearable.
					ledcom.send_command(message_text)
				else:
					if(censorship==False or is_from_moderator(next_filter_match)):
						scrollText=True 	# otherwise, it will be displayed as text
						colorator.parse_colors(message_text) # extract color information and set the color mapper accordingly
						scroll_time,scroll_buffer=render_text(next_filter_match['text']) #set an initial text
					else:
						print('Message ignored due to moderator constraints')
			else:
				printNicely("-- Some data: " + str(next_filter_match))
			print ("Twitter OK")
			if(scrollText):
				while ( not is_scroll_finished()):
					print ("Scrolling Message")
					old_time=time.time()
					send_data=get_scrolled_pixel_data()
					print ('until data ready took:'+str(time.time()-old_time))
					ledcom.send_bytearray(send_data)
					print ('until sending finished took:'+str(time.time()-old_time))
					#print(scroll_buffer)
				scrollText= False
			else:
				print ("Showing Effect")
				ledcom.send_keep_alive(); # give the wearable a sign that we still exist...
	except Exception as e:
		print('!!!Twitter connection failure - wait 2 minutes, check network and restart Pi!!!');
		print(str (e))
		scroll_time,scroll_buffer=render_text('!!!Twitter connection failure - check network and restart Pi!!!') #set text
		startTime=time.time()
		# show error message and try again...
		while (time.time()-startTime<30):
			ledcom.send_bytearray(get_scrolled_pixel_data())