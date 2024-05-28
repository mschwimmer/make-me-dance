from itertools import chain
from functools import wraps
import logging, sys
import pandas as pd
from config import get_config
import user_functions
from flask import Flask, url_for, session, request, redirect, flash, jsonify, after_this_request
from flask import render_template
from flask_mail import Mail, Message
from utils.email_validation import is_valid_email, domain_exists
from spotipy.oauth2 import SpotifyOAuth
import time
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create and configure Flask App
app = Flask(__name__)
app.config.from_object(get_config())
data_folder = os.path.join(app.root_path, 'data')
mail = Mail(app)


def get_headers_size(headers):
    headers_str = ''.join(f"{key}: {value}\n" for key, value in headers.items())
    return sys.getsizeof(headers_str.encode('utf-8'))


def measure_response_size(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        @after_this_request
        def measure_response(response):
            # Measure payload size
            response_data = response.get_data()
            payload_size_bytes = sys.getsizeof(response_data)
            payload_size_megabytes = payload_size_bytes / (1024 * 1024)

            # Measure headers size
            headers_size_bytes = get_headers_size(response.headers)
            headers_size_megabytes = headers_size_bytes / (1024 * 1024)

            # Measure cookies size
            cookies_str = ''.join(f"{key}: {value}\n" for key, value in request.cookies.items())
            cookies_size_bytes = sys.getsizeof(cookies_str.encode('utf-8'))
            cookies_size_megabytes = cookies_size_bytes / (1024 * 1024)

            total_size_megabytes = payload_size_megabytes + headers_size_megabytes + cookies_size_megabytes

            # print(f"Payload size: {payload_size_megabytes:.2f} MB")
            # print(f"Headers size: {headers_size_megabytes:.2f} MB")
            # print(f"Cookies size: {cookies_size_megabytes:.2f} MB")
            # print(f"Payload size: {payload_size_bytes} bytes")
            # print(f"Headers size: {headers_size_bytes} bytes")
            # print(f"Cookies size: {cookies_size_bytes} bytes")
            print(f"Total response size for {request.endpoint}: {total_size_megabytes:.2f} MB")

            return response

        return func(*args, **kwargs)
    return wrapper


@app.route('/')
@measure_response_size
def index():
    session.clear()
    print("Displaying index page")
    return render_template("index.html")


@app.route('/login')
@measure_response_size
def login():
    session.clear()
    print("Logging in")
    sp_oath = create_spotify_oath()
    auth_url = sp_oath.get_authorize_url()
    session['token_info'] = sp_oath.get_cached_token()
    print(f"auth_url: {auth_url}")
    return redirect(auth_url)


@app.route('/authorize')
@measure_response_size
def authorize():
    sp_oath = create_spotify_oath()
    session.clear()
    # Storing authorization code from oath
    code = request.args.get('code')
    # Using auth code to get access token
    token_info = sp_oath.get_access_token(code)
    # Apparently future versions of library will return the straight-up string, not a dict
    # So, handle either way
    if isinstance(token_info, str):
        session["token_info"]['access_token'] = token_info
    elif isinstance(token_info, dict):
        session["token_info"] = token_info
    else:
        raise TypeError("Unexpected type for token_info")
    return redirect(url_for('welcome', _external=True))


@app.route('/welcome')
@measure_response_size
def welcome():
    session['token_info'], authorized = get_token()
    session.modified = True
    if not authorized:
        print("User not authorized, redirecting to index page")
        return redirect('/')

    access_token = session['token_info']['access_token']
    session['user_data'] = user_functions.get_user_data(access_token)
    print("Created access token, sending user to welcome page")
    return render_template("welcome.html", user_data=session['user_data'])


@app.route('/request-beta', methods=["GET", "POST"])
@measure_response_size
def request_beta():
    if request.method == 'POST':
        name = request.form["name"]
        email = request.form["email"]

        # Validate email
        # TODO handle invalid form input is a good way
        if not is_valid_email(email):
            return redirect(url_for('request_beta'))
        if not domain_exists(email):
            return redirect(url_for('request_beta'))

        # Send Beta Request Email
        try:
            msg = Message('Beta Access Request', recipients=['mschwimmer1234@gmail.com'])
            msg.body = f"Name: {name}\n Email: {email}\n just sent a beta request from make me dance"
            mail.send(msg)
            # TODO handle successful beta request in a good way
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            flash('Failed to send your beta request, please try again later', 'danger')

        return redirect(url_for('request_beta'))

    return render_template("request-beta.html")


@app.route('/user-playlists')
@measure_response_size
def get_user_playlists():
    print("Gathering user's playlists")
    access_token = session['token_info']['access_token']
    playlists_data = user_functions.get_user_playlists(access_token)

    # Safeguard against bad data
    items = playlists_data.get("items", [])
    if not items:
        print("Couldn't find items in playlist data :(")
        return pd.DataFrame()

    print(f"Parsing user's playlist data")
    playlists = []
    for item in items:
        try:
            playlist = {'playlist_name': item['name'], 'playlist_id': item['id'],
                        'track_total': item['tracks']['total'], 'playlist_href': item['href']}
            playlists.append(playlist)
        except KeyError as e:
            print(f"KeyError while extracting playlist data {e}")

    return playlists


@app.route('/playlist-items', methods=["POST"])
@measure_response_size
def get_playlist_items():
    print("Gathering playlist items")
    access_token = session['token_info']['access_token']
    playlists = request.json
    if not playlists or not isinstance(playlists, list):
        return jsonify({'error': 'Invalid input data'}), 400
    playlists = user_functions.get_all_playlist_items(access_token, playlists)
    # TODO the total response size was 43 MB, need to make smaller
    return playlists


@app.route('/song-list', methods=["POST"])
@measure_response_size
def generate_song_list():
    print("Parsing playlist items to create song list")
    playlists = request.json
    songs = user_functions.get_song_list(playlists)
    return songs


@app.route('/song-data', methods=["POST"])
@measure_response_size
def get_song_batch_data():
    print(f"Gathering song batch data")
    access_token = session['token_info']['access_token']
    songs = request.json

    unique_track_data = user_functions.get_many_tracks_data(access_token, list(songs.keys()))
    flat_track_data = list(chain.from_iterable(unique_track_data))
    flat_track_data = [track for track in flat_track_data if track is not None]
    return flat_track_data


@app.route('/dance-songs', methods=["POST"])
@measure_response_size
def get_dance_songs():
    print(f"Returning top 30 dance songs")
    songs = request.json['songs']
    flat_track_data = request.json['song_data']
    for track_data in flat_track_data:
        if track_data['id'] in songs:
            songs[track_data['id']]['danceability'] = track_data['danceability']
    song_df = pd.DataFrame.from_dict(songs, orient='index')
    song_df = song_df[~song_df['track_name'].duplicated()]
    dance_df = song_df.sort_values('danceability', ascending=False).iloc[0:30]
    dance_df.reset_index(drop=True, inplace=True)

    dance_json = dance_df.to_json(orient="records")
    return dance_json


@app.route('/display-dance-songs')
@measure_response_size
def display_dance_songs():
    return render_template("display-dance-songs.html")


@app.route('/create-dance-playlist', methods=['POST'])
@measure_response_size
def create_dance_playlist():
    access_token = session['token_info']['access_token']
    if 'user_data' not in session:
        session['user_data'] = user_functions.get_user_data(access_token)
    user_name = session['user_data']['display_name'].lower().replace(' ', '_')
    file_path = os.path.join(data_folder, f"{user_name}_song_data.csv")

    # Get user's dance songs
    if os.path.exists(file_path):
        # User's dance song data file already exists, load from file and send to page
        song_df = pd.read_csv(file_path)
    else:
        # User's dance songs must be gathered and stored as file
        song_df = user_functions.get_user_songs(access_token)
        # TODO use some sort of basic database for storing user's data
        #  because vercel is serverless, so you can't save anything
        # song_df.to_csv(file_path, index=False)

    dance_df = song_df.sort_values('danceability', ascending=False).iloc[0:30]

    playlist_name = request.form['playlist_name']
    # If you're ever modifying the session, need to set this
    session.modified = True
    session['created_playlist'] = False

    # Check if user already has playlist with same name
    playlist_data = user_functions.get_user_playlists(access_token)

    if playlist_name not in [item['name'] for item in playlist_data['items']]:
        # Collect list of top 30 dance track URIs
        track_uris = dance_df['uri'].to_list()
        # Create new playlist for user
        playlist_response = user_functions.create_playlist(access_token, session['user_data']['id'], playlist_name)
        # Add 30 dance tracks to new playlist
        add_tracks_response = user_functions.add_tracks_to_playlist(access_token, playlist_response['id'], track_uris)
        session['new_playlist_link'] = playlist_response['external_urls']['spotify']
        session['created_playlist'] = True
        print(f"Created new playlist {playlist_response['external_urls']['spotify']}")
    else:
        print(f"Did not create new playlist")

    print("Redirecting to result page")
    print(f"Session keys BEFORE redirect: {session.keys()}")
    return redirect(url_for('playlist_result'))


@app.route('/playlist-result')
@measure_response_size
def playlist_result():
    # created_playlist = session.get('created_playlist', False)
    print(f"Session keys AFTER redirect: {session.keys()}")
    return render_template("playlist-result.html")


def get_token():
    token_valid = False
    token_info = session.get("token_info", {})

    # Checking if the session already has a token stored
    if not session.get("token_info", False):
        token_valid = False
        return token_info, token_valid

    # Checking if token is expired
    now = int(time.time())
    is_token_expired = session.get('token_info').get('expires_at') - now < 60

    # Refreshing token if expired
    if is_token_expired:
        print("Token is expired, generating new one!")
        sp_oath = create_spotify_oath()
        token_info = sp_oath.refresh_access_token(session.get('token_info').get('refresh_token'))

    token_valid = True
    return token_info, token_valid


def create_spotify_oath():
    spotify_redirect_uri = app.config['SPOTIFY_REDIRECT_URI']
    print(f"Redirect URI: {spotify_redirect_uri}")
    print(f"Whatever url_for produces for authorize: {url_for('authorize', _external=True)}")

    return SpotifyOAuth(
        client_id=app.config['SPOTIFY_CLIENT_ID'],
        client_secret=app.config['SPOTIFY_CLIENT_SECRET'],
        redirect_uri=url_for('authorize', _external=True),
        scope="user-top-read playlist-modify-public playlist-modify-private playlist-read-private"
    )





if __name__ == '__main__':
    app.run()
