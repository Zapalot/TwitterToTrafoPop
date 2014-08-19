#We need all this stuff in order to receive twitter message streams

# A note to the interested reader:
# The twitter package directly constructs urls from the attribute names instead of implementing member functions.
# So you will not find i.e. "statuses" or "filter" anywhere in the sourcecode of the module.
# all of it is implemented in the 'TwitterCall' class if you dare to look at something that might disturb you...

	
import os
from twitter.stream import TwitterStream, Timeout, HeartbeatTimeout, Hangup
from twitter.oauth import OAuth
from twitter.util import printNicely
from twitter import *

def get_twitter_stream():
	MY_TWITTER_CREDS = os.path.expanduser('~/.my_app_credentials')  #once we have obtained twitter credentials by the oauth dance, we save them here for reuse.

	#these are the API keys we use to authenticate our application against twitter. 
	CONSUMER_KEY='idpNqIbznmlvWoTAFlum5s4Z7'
	CONSUMER_SECRET='dYfMgEpBCvyd9U92WED76sRrx2aAgj7MePizd5LxqTNDhw6lLp'

	#if we haven't gotten oauth credentials yet, we get them now. This will invoke a web-browser!
	if not os.path.exists(MY_TWITTER_CREDS):
		oauth_dance("My App Name", CONSUMER_KEY, CONSUMER_SECRET,
					MY_TWITTER_CREDS)

	# read OAuth credentials and setup an authenication instance for later use
	oauth_token, oauth_secret = read_token_file(MY_TWITTER_CREDS)
	twitter_auth=OAuth(oauth_token, oauth_secret, CONSUMER_KEY, CONSUMER_SECRET)
		

	#create an interface to the twitter streaming api
	twitter_stream = TwitterStream(auth=twitter_auth,timeout=0.01) # we set a short timeout to allow scrolling

	return twitter_stream
