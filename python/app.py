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
    session.clear()
    print("Logging in")
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
def user_dance_songs():
    access_token = session['token_info']['access_token']
    if 'dance_songs' not in session:
        # User's dance songs are not yet in session, must retrieve
        song_df = user_functions.get_user_songs(access_token)
        dance_df = user_functions.get_top_dance_songs(song_df, 30)
        session['dance_songs'] = dance_df[['track_name', 'album', 'artist', 'plist_name', 'danceability', 'uri']].to_dict(
            orient='records')

    return render_template("dance-songs.html")


@app.route('/create-dance-playlist', methods=['POST'])
def create_dance_playlist():
    access_token = session['token_info']['access_token']
    if 'dance_songs' not in session:
        # User's dance songs are not yet in session, must retrieve
        song_df = user_functions.get_user_songs(access_token)
        dance_df = user_functions.get_top_dance_songs(song_df, 30)
        session['dance_songs'] = dance_df[['track_name', 'album', 'artist', 'plist_name', 'danceability', 'uri']].to_dict(
            orient='records')

    playlist_name = request.form['playlist_name']
    # Check if user already has playlist with same name
    if 'playlist_data' not in session:
        session['playlist_data'] = user_functions.get_user_playlists(access_token)
    if playlist_name not in [item['name'] for item in session['playlist_data']['items']]:
        # Collect list of top 30 dance track URIs
        track_uris = [song['uri'] for song in session['dance_songs']]
        # Create new playlist for user
        playlist_response = user_functions.create_playlist(access_token, session['user_data']['id'], "My Dance Playlist")
        # Add 30 dance tracks to new playlist
        add_tracks_response = user_functions.add_tracks_to_playlist(access_token, playlist_response['id'], track_uris)
        session['playlist_success'] = True
    else:
        session['playlist_failure'] = True

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
    return SpotifyOAuth(
        client_id=config.client_id,
        client_secret=config.client_secret,
        redirect_uri=url_for('authorize', _external=True),
        scope="user-top-read playlist-modify-public playlist-modify-private"
    )


if __name__ == '__main__':
    app.run(debug=True)
