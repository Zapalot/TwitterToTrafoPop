#####################################
###
# Setup connection to the led-wearable.
# The pySerial module is used for this purpose.
# Default Baudrate is 115200
########################################
import time

# Setup message parsing system
########################################
from messageparsing  import *
colorator = ColorMapper() #this guy will look for color commands and colorize our bitmaps accordingly
scrollText=True #set False after sending an effect command
########################################
# Load LED-positions from file and create an object that will map pixel positions to led indices
########################################
########################################
# Setup the font-rendering system.
########################################


########################################
# Setup twitter connectivity
########################################
import twittersetup #we have put all the details into a separate file. Look here to change credentials.
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup

def get_user_name(tweet):
	if(tweet.get('text')):
		if(tweet.get('user')):
			if tweet.get('user').get('screen_name'): return tweet.get('user').get('screen_name')
	return none

	
	
moderator_names=['trafopopAutomat'] # a List of screen names that are allowed to show messages even if cencorship is enabled
censorship=False

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
	if tweet.get('text').find('offen für alle')>0:
		print ('Viel Spaß Kids!')
		return False

	


########################################
# receive until the end of days... - we've put everything into a try block and a loop to minimize potential for trouble at the show...
########################################
while(1):
	print ("trying to connect to twitter...")
	#try to establish a connection to twitter.
	
	twitter_stream=twittersetup.get_twitter_stream() #twittersetup.py contains all the details..
	# Get a python iterator that will stream all tweets matching certain filter criteria to us.
	filter_args = dict() # all the parameters of the query are put in this dictionary
	filter_args['track'] = '@TrafoPopTest' # 'track' is a Twitter API parameter explained here:https://dev.twitter.com/docs/streaming-apis/parameters#track
	tweet_iter = twitter_stream.statuses.filter(**filter_args) # this establishes the connection to twitter
	print ("twitter connection successful ...")
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
		elif next_filter_match is Hangup:
			print("-- Hangup --")
		elif next_filter_match.get('text'):
			print('###########'+get_user_name(next_filter_match))
			message_text=next_filter_match['text']# extract message content and convert to plain ascii
			print(message_text.encode(encoding='ascii',errors='ignore') ) #for debug purposes...
			censorship=get_cencorship_from_message(next_filter_match) # moderator control
			#if(next_filter_match['screen_name']=='trafopopAutomat'):
			#	print ("Ja meister?!")
			#check if the message contains a command. A list of them is contained in 'messageparsing.py'
			#if (containsCommand(message_text)) 0
		else:
			printNicely("-- Some data: " + str(next_filter_match))