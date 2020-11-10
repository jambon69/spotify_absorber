#!/usr/bin/env python

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from youtube_search import YoutubeSearch
import requests
import time
import os

spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
spotify_user_id = os.getenv("SPOTIFY_USER_ID", "username")

youtube_to_mp3_token = "eyJpdiI6IktsSE1RQ0FUSEpMOTBpMXdPaXdnWEE9PSIsInZhbHVlIjoiUVJkTjZFSkNTY0ppa0x5MU9pWjZrZz09IiwibWFjIjoiYjg3YTQ4OGJmMDUyOWY5MWU2ZWE2MmY2YmQzMWJhMTkwY2I1ZWZkNmQ0NGI5Y2ZiMTVlMTAxZTAwNWIzZmNlMCJ9"

sp = None

def authenticate():
    global sp

    scope = "playlist-read-private user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, client_id=spotify_client_id,
                                                   client_secret=spotify_client_secret,
                                                   redirect_uri="http://localhost:8080"))
    return sp.user(spotify_user_id)

def get_current_user_playlists():
    return (sp.current_user_playlists())

def get_playlist_tracks(playlist):
    limit = playlist['tracks']['total']
    return (sp.playlist_tracks(playlist['id']))

def ask_youtube(name):
    results = YoutubeSearch(name, max_results=1).to_dict()
    return (f"https://youtube.com{results[0]['url_suffix']}")

def download_youtube(video_url, fileName):
    print(video_url)
    r = requests.post("https://mp3-youtube.download/download/start", data={
        "url": video_url,
        "extension": "mp3"
    }, headers={
        "X-Token": youtube_to_mp3_token
    })
    uuid = r.json()['data']['uuid']
    print(f"UUID: {uuid}")

    while True:
        r = requests.get(f"https://mp3-youtube.download/download/{uuid}", headers={
            "X-Token": youtube_to_mp3_token
        })
        fileUrl = r.json()['data']['fileUrl']
        if fileUrl:
            break
        else:
            print("Waiting for youtube to mp3...")
        if r.json()['data']['error']:
            print(f"Error: {r.json()['data']['error']}")
            return
        time.sleep(1)

    print(f"Downloading file: {fileName}")
    r = requests.get(fileUrl)
    with open(fileName, 'wb') as f:
        f.write(r.content)
        

def main():
    user = authenticate()

    print(f"User connected: {user['display_name']}")

    user_playlists = get_current_user_playlists()

    playlists_blacklist = [] # use this arrey if you don't want some playlists
    
    for playlist in user_playlists['items']:
        print("-"*50)
        print(f"Playlist NAME: {playlist['name']}")
        if playlist['name'] in playlists_blacklist:
            print("Not going to download this playlist")
            continue
        try:
            os.makedirs(f"playlists/{playlist['name']}")
        except:
            pass
        print("-"*50)
        print("Tracks:")
        for track in get_playlist_tracks(playlist)['items']:
            custom_name = f"{track['track']['name']} - {' '.join(elem['name'] for elem in track['track']['artists'])}"
            print(f"\t - {custom_name}")
            file_name = f"playlists/{playlist['name']}/{custom_name.replace(' ', '_')}.mp3"
            if os.path.isfile(file_name):
                print(f"\t - {file_name}: already exists")
                continue
            try:
                url = ask_youtube(custom_name)
                download_youtube(url, file_name)
            except:
                print("Couldn't download from youtube :(")
            print("-"*20)
main()
