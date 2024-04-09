import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session,redirect
import os
import requests
from dotenv import load_dotenv
import time
import pandas as pd
from flask import jsonify

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
    return redirect(url_for('get_favorite_tracks',external = True))



@app.route('/GetFavoriteTracks')
def get_favorite_tracks():
    try:
        token_info = get_token()
    except:
        print('User not logged in')
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    track_ids = []
    
    #Pega as primeiras 50 músicas
    top_tracks_1 = sp.current_user_top_tracks(limit=50, time_range='short_term')['items']
    track_ids += [track['id'] for track in top_tracks_1]
    
    #Se ja tiverem 50 músicas, pega as outras 50 para completar 100
    if len(top_tracks_1) == 50:
        top_tracks_2 = sp.current_user_top_tracks(limit=50, offset=50, time_range='short_term')['items']
        track_ids += [track['id'] for track in top_tracks_2]
    
    top_tracks = top_tracks_1 + top_tracks_2
        
    audio_features = sp.audio_features(track_ids)
    
    # Create a DataFrame from the audio features
    df = pd.DataFrame(audio_features)
    df['track_name'] = [track['name'] for track in top_tracks['items']]
    df['track_artist'] = [track['artists'][0]['name'] for track in top_tracks]
    
    return "Faixas obtidas e analisadas. Use /AnalysisResult para ver a análise."

   


def get_token():
    token_info = session.get(TOKEN_INFO,None)
    if not token_info:
        redirect(url_for('login',external = False))
        
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 30
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info
    



def create_spotify_oauth():
    return SpotifyOAuth(
        client_id= client_id,
        client_secret= client_secret,
        redirect_uri=url_for('redirect_page', _external=True),
        scope = "user-library-read playlist-modify-public playlist-modify-private user-top-read"
    )

app.run(debug=True)