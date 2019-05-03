from flask import Flask, request, render_template, session
import spotipy
import spotipy.util as util
import psycopg2
import os

connection = psycopg2.connect(user = "postgres", password = os.environ.get('DB_PASSWORD'), host = "127.0.0.1", port = "5432", database = "postgres")

cur = connection.cursor()
from .api_functions import authenticate_spotify, create_playlist, get_emotion

spot_client_id = os.environ.get('SPOT_CLIENT_ID')
spot_client_secret = os.environ.get('SPOT_CLIENT_SECRET')
redirect_uri = 'https://localhost:8080/'

scope = 'user-library-read user-top-read playlist-modify-public user-follow-read'

app = Flask(__name__)
app.secret_key = 'some secret key'

#attempt to clear cache
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
    #post method - retrieve spotify username entered by the user
    if request.method == 'POST':
        spotify_user = request.form['name']
        session['spotify_user'] = spotify_user
        
        #create a token that authorizes the session
        session['token'] = util.prompt_for_user_token(spotify_user, scope, spot_client_id, spot_client_secret, redirect_uri)
        sp = spotipy.Spotify(auth=session.get("token",None))
        user_all_data = sp.current_user()
        user_id = user_all_data["id"]
        print(user_id)
        return render_template("home.html")
    #returning to home page
    else:
        return render_template("home.html")
    
@app.route('/view', methods = ['POST', 'GET'])
def view():
    #vuew number of playlists created
    spotify_user = session.get("spotify_user", None)
    
    #query
    sql = "SELECT * FROM public.playlist_data WHERE username = '%s'" % spotify_user
    cur.execute(sql)
    playlist_data = cur.fetchall()
    num = len(playlist_data)
    return render_template("view.html", num=num)

@app.route('/generate', methods = ['POST', 'GET'])
def generate():
    #generate a playlist using tweets
    if request.method == 'POST':
        #retrieve twitter handle input by the user
        name = request.form['name']
        emotion = get_emotion(name)
        
        #use emotion to generate playlist
        token = session.get('token', None)
        spotify_auth = authenticate_spotify(token)
        playlist = create_playlist(spotify_auth, emotion, name)
        return render_template("generate.html")