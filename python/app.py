import config
import user_functions
from flask import Flask, url_for, session, request, redirect
from flask import render_template
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
    return redirect(url_for('welcome', _external=True))


@app.route('/welcome')
def welcome():
    session['token_info'], authorized = get_token()
    session.modified = True
    if not authorized:
        return redirect('/')

    access_token = session['token_info']['access_token']
    session['user_data'] = user_functions.get_user_data(access_token)

    return render_template("welcome.html", user_data=session['user_data'])


@app.route('/artist-game')
def enter_game():
    access_token = session['token_info']['access_token']
    session['user_data'] = user_functions.get_user_data(access_token)
    session['playlist_data'] = user_functions.get_user_playlists(access_token)
    session['game_data'] = user_functions.guess_song_game(access_token)
    # TODO get user input from three buttons
    return render_template("artist-game.html", user_data=session['user_data'], game_data=session['game_data'])


@app.route('/user-guess', methods=['POST'])
def handle_guess():
    user_guess = request.form['guess']
    if user_guess == session['game_data']['correct_album']:
        return f"{user_guess} IS CORRECT!"
    else:
        return f"{user_guess} IS INCORRECT, IT WAS ACTUALLY {session['game_data']['correct_album']}"


@app.route('/user-dance-songs')
def display_user_dance_songs():
    access_token = session['token_info']['access_token']
    song_df = user_functions.get_user_songs(access_token)
    dance_songs = user_functions.get_top_dance_songs(song_df, 30)

    return render_template("dance-songs.html")


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


if __name__ == '__main__':
    app.run(debug=True)
