from flask import Flask, json, request, render_template, redirect, session
import tweepy
from ibm_watson import ToneAnalyzerV3

import sys
import spotipy
import spotipy.util as util

import random
import psycopg2

connection = psycopg2.connect(user = "postgres", password = "abhamofo", host = "127.0.0.1", port = "5432", database = "postgres")

cur = connection.cursor()
#from api_functions import authenticate_spotify, create_playlist

#app = Flask(__name__)
# Load our config from an object, or module (config.py)

#app.config.from_object('config')

TWITTER_CONSUMER_KEY = 'vDB8EbdZAqzgpNoXzkxG8kkv6'
TWITTER_CONSUMER_SECRET = 'K7DIcCspXismWxZjU9KB4jdX0WOJS1JkHsqTX8iqChuHMLn9tj'
TWITTER_ACCESS_TOKEN = '782072042619215872-WNz8dJi1dY4mMGgNlYSx7MoeJbxtSWY'
TWITTER_ACCESS_TOKEN_SECRET = 'wyoot9T6ukOsE0Wz9fISUAPg05rFC4pFg58lgOR0kOvW9'

# These config variables come from 'config.py'
auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
tweepy_api = tweepy.API(auth)

ta_username = 'apikey'
ta_password = 'eoVcBFdhSvjq5bXyOR9inUc75E_TEUwlZ90eLVT2aHE6'

client_id = '35acf306c8dd4e9384ce0819f058e844'
client_secret = 'aa720c6d7bae46b0901f19078ade5326'
redirect_uri = 'https://localhost:8080/'

scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'

#spotify_user = 'marydao97'
#token = util.prompt_for_user_token(spotify_user, scope, client_id, client_secret, redirect_uri)

def authenticate_spotify(token):
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
    
    playlist_name = "Playlist - " + username
    playlist_all_data = sp.user_playlist_create(user_id, playlist_name)
    playlist_id = playlist_all_data["id"]
    playlist_uri = playlist_all_data["uri"]
    
    random.shuffle(song_uris)
	# try:
    sp.user_playlist_add_tracks(user_id, playlist_id, song_uris)
    sql = "INSERT INTO public.playlist_data(username, playlist) VALUES(%s, %s)"
    cur.execute(sql, [user_id, playlist_name])
    connection.commit()
    return playlist_uri


app = Flask(__name__)
app.secret_key = 'some secret key'

@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
    
@app.route('/', methods = ['POST', 'GET'])
def hello_world():
    return render_template("index.html")

@app.route('/tweet', methods = ['POST', 'GET'])
def tweet():
    if request.method == 'POST':
        spotify_user = request.form['name']
        session['spotify_user'] = spotify_user
        session['token'] = util.prompt_for_user_token(spotify_user, scope, client_id, client_secret, redirect_uri)
        sp = spotipy.Spotify(auth=session.get("token",None))
        user_all_data = sp.current_user()
        user_id = user_all_data["id"]
        print(user_id)
        return render_template("home.html")
    else:
        return render_template("home.html")
    
@app.route('/view', methods = ['POST', 'GET'])
def view():
    spotify_user = session.get("spotify_user", None)
    sql = "SELECT * FROM public.playlist_data WHERE username = '%s'" % spotify_user
    cur.execute(sql)
    playlist_data = cur.fetchall()
    num = len(playlist_data)
    return render_template("view.html", num=num)

@app.route('/generate', methods = ['POST', 'GET'])
def generate():
    if request.method == 'POST':
        name = request.form['name']
        tweets = tweepy_api.user_timeline(name, count=10)   
    
    # Initialize Tone Analyzer SDK
        tone_analyzer = ToneAnalyzerV3(version='2017-09-21', iam_apikey=ta_password, url='https://gateway-wdc.watsonplatform.net/tone-analyzer/api')
        scores = [0, 0, 0, 0, 0]
    # Iterate through each Tweet
        for index, s in enumerate(tweets):

        # Analyize the Tweet string
            tone_analysis = tone_analyzer.tone({'text': s.text}, content_type='application/json').get_result()     
            document_tone = tone_analysis["document_tone"]
            for tone_categories in document_tone["tones"]:

            # Store emotional attributes
                emotions = {}
            #if tone_categories["tone_id"] == "emotion_tone":
                if len(tone_categories) > 0:
                #print(str(tone_categories["tone_name"]) + ": " + str(round(tone_categories["score"] * 100, 2)))
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
    
        emotions = ['joy', 'anger', 'fear', 'sadness', 'disgust']
        emotion = emotions[int(scores.index(max(scores)))]
        
        token = session.get('token', None)
        spotify_auth = authenticate_spotify(token)
        playlist = create_playlist(spotify_auth, emotion, name)
        return render_template("generate.html")