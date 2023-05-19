import config
import spotify_functions as sf
# Game
# Step 1, get the top artist of the user
# Step 2, pick a random song from an artist
# Step 3, pick 3 albums
# Step 4, let the user pick the right album


def get_user_id():
    return config.user_id


def get_all_songs_from_playlists():
    ...


def get_playlists_from_user(user_id):
    user_playlists = sp.get_user_playlists(token, user_id)
    # TODO test if this works
    ...


def get_random_song():
    # Eventually this function will return a random song from the user's top artist
    ...


def get_choices_from_song():
    # Eventually this function will get the three album choices that the user can pick from
    ...


if __name__ == '__main__':
    token = config.get_token()
    user_id = get_user_id()
    top_artist = sf.get_top_artist(token, user_id)
    print(top_artist)

