import tweepy
import spotipy
import spotipy.util as util
import sys
from ibm_watson import ToneAnalyzerV3
import os

import random

def authenticate_spotify(token):
	#authenticate spotify user using a generated token
	sp = spotipy.Spotify(auth=token)
	return sp

def create_playlist(sp, emotion, username):
    tone_search = sp.search(emotion,limit=10,offset=0,type="playlist")

    #Unicode map to deal with emojis in playlist titles
    non_bmp_map = dict.fromkeys(range(0x10000, sys.maxunicode + 1), 0xfffd)
    
    #Get playlist name and id
    playlist_info = [[0 for x in range(10)], [0 for x in range(10)]]
    playlists = tone_search['playlists']
    for i, item in enumerate(playlists['items']):
        playlist_info[0][i] = item['id']
        playlist_info[1][i] = item['name'].translate(non_bmp_map)
    
    #Choose a random playlist and get its songs
    playlist_number = random.randint(0,9)
    playlist_songs = sp.user_playlist_tracks("spotify",playlist_info[0][playlist_number])
    song_list = playlist_songs['items']
    
    #Filter to only get songs with a link to a 30 second preview
    playable_song_list = []
    for i, song in enumerate(song_list):
        if (song['track']['preview_url']) == None:
            next(enumerate(song_list))
        else:
            playable_song_list.append(song)
        
    #print(playable_song_list)
    song_uris = []        
    for x, track in enumerate(playable_song_list):
        song_uris.append(track['track']['uri'])
        
    user_all_data = sp.current_user()
    user_id = user_all_data["id"]
    
    #retrieve playlist data
    playlist_all_data = sp.user_playlist_create(user_id, "Playlist - " + username)
    playlist_id = playlist_all_data["id"]
    playlist_uri = playlist_all_data["uri"]
    
    #create playlist in user library
    random.shuffle(song_uris)
	# try:
    sp.user_playlist_add_tracks(user_id, playlist_id, song_uris)
    return playlist_uri

def get_emotion(name):
    TWITTER_CONSUMER_KEY = os.environ.get('TWITTER_CONSUMER_KEY')
    TWITTER_CONSUMER_SECRET = os.environ.get('TWITTER_CONSUMER_SECRET')
    TWITTER_ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
    TWITTER_ACCESS_TOKEN_SECRET = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
    
    auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    tweepy_api = tweepy.API(auth)
    tweets = tweepy_api.user_timeline(name, count=10) 
    
    ta_password = os.environ.get('TA_PASSWORD')
    #initialize tone analyzer SDK
    tone_analyzer = ToneAnalyzerV3(version='2017-09-21', iam_apikey=ta_password, url='https://gateway-wdc.watsonplatform.net/tone-analyzer/api')
    scores = [0, 0, 0, 0, 0]
    #iterate through each tweet
    for index, s in enumerate(tweets):

        #retrieve tone analysis
        tone_analysis = tone_analyzer.tone({'text': s.text}, content_type='application/json').get_result()     
        document_tone = tone_analysis["document_tone"]
        for tone_categories in document_tone["tones"]:

            if len(tone_categories) > 0:
                if str(tone_categories["tone_name"]) == 'Joy':
                    scores[0] += round(tone_categories["score"] * 100, 2)
                if str(tone_categories["tone_name"]) == 'Anger':
                    scores[1] += round(tone_categories["score"] * 100, 2)
                if str(tone_categories["tone_name"]) == 'Fear':
                    scores[2] += round(tone_categories["score"] * 100, 2)
                if str(tone_categories["tone_name"]) == 'Sadness':
                    scores[3] += round(tone_categories["score"] * 100, 2)
                if str(tone_categories["tone_name"]) == 'Disgust':
                    scores[4] += round(tone_categories["score"] * 100, 2)
        
        #determine dominant emotion                
    emotions = ['joy', 'anger', 'fear', 'sadness', 'disgust']
    emotion = emotions[int(scores.index(max(scores)))]
    return emotion