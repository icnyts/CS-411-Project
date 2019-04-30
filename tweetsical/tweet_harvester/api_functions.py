# -*- coding: utf-8 -*-
"""
Created on Fri Apr 26 00:19:30 2019

@author: durus
"""

import spotipy
import spotipy.util as util
import sys

import random



def authenticate_spotify(token):
	print('...connecting to Spotify')
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
    
    playlist_all_data = sp.user_playlist_create(user_id, "Playlist - " + username)
    playlist_id = playlist_all_data["id"]
    playlist_uri = playlist_all_data["uri"]
    
    random.shuffle(song_uris)
	# try:
    sp.user_playlist_add_tracks(user_id, playlist_id, song_uris)
    return playlist_uri