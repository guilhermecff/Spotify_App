import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect, jsonify
import os
import requests
from dotenv import load_dotenv
import time
import pandas as pd

load_dotenv()

client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'
app.secret_key = 'gadiaf76578bfa*5bfaf*'
TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('get_favorite_tracks', external=True))

@app.route('/GetFavoriteTracks')
def get_favorite_tracks():
    try:
        token_info = get_token()
    except:
        print('User not logged in')
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    track_ids = []
    tracks_info = []
    genres_list = []
    
    # Retrieve top tracks
    for offset in range(0, 500, 50):
        results = sp.current_user_top_tracks(limit=50, offset=offset, time_range='medium_term')
        top_tracks = results['items']
        if not top_tracks:
            break
        for track in top_tracks:
            track_ids.append(track['id'])
            tracks_info.append(track)
            # Retrieve genres from artists of each track
            genres = []
            for artist in track['artists']:
                artist_details = sp.artist(artist['id'])
                genres.extend(artist_details['genres'])
            genres_list.append(genres)

    # Fetch audio features for all collected track IDs in batches
    audio_features = get_audio_features(sp, track_ids)
    df_audio_features = pd.DataFrame(audio_features)

    # Create DataFrame for tracks info
    df_tracks = pd.DataFrame(tracks_info)
    
    # Simplifying the tracks DataFrame to essential info and adding genres
    df_tracks = df_tracks[['id', 'name', 'popularity', 'album']]
    df_tracks['genres'] = genres_list

    # Merge DataFrames on 'id'
    df_final = pd.merge(df_tracks, df_audio_features, on='id', how='left')

    df_final.to_csv('df.csv', index=False)

    return "Tracks fetched and analyzed."

def get_audio_features(sp, track_ids):
    max_ids_per_request = 100
    audio_features = []
    for i in range(0, len(track_ids), max_ids_per_request):
        batch_ids = track_ids[i:i+max_ids_per_request]
        results = sp.audio_features(batch_ids)
        audio_features.extend(results)
    return audio_features

def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        return redirect(url_for('login', external=False))
    
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 30
    if is_expired:
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=url_for('redirect_page', _external=True),
        scope="user-library-read playlist-modify-public playlist-modify-private user-top-read"
    )

app.run(debug=True)