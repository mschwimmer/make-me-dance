import config
import spotify_functions as sf
from flask import Flask, url_for, session, request, redirect
from flask import render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time


app = Flask(__name__)
app.secret_key = config.flask_secret_key
app.config['SESSION_COOKIE_NAME'] = config.flask_session_name


@app.route('/')
def login():
    sp_oath = create_spotify_oath()
    auth_url = sp_oath.get_authorize_url()
    print(auth_url)
    return redirect(auth_url)


@app.route('/authorize')
def authorize():
    sp_oath = create_spotify_oath()
    session.clear()
    # Storing authorization code from oath
    code = request.args.get('code')
    # Using auth code to get access token
    token_info = sp_oath.get_access_token(code)
    session["token_info"] = token_info
    return redirect(url_for('get_tracks', _external=True))


@app.route('/getTracks')
def get_tracks():
    session['token_info'], authorized = get_token()
    session.modified = True
    session["test_key"] = "test value"
    if not authorized:
        return redirect('/')

    print(session)
    print(sf.get_top_artist(session['token_info']['access_token']))
    # The token_info key in session is our spotify API token
    return "some songs or something"


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
    return SpotifyOAuth(
        client_id=config.client_id,
        client_secret=config.client_secret,
        redirect_uri=url_for('authorize', _external=True),
        scope="user-top-read"
    )


