import config
import spotify_functions as sf


def get_user_data(access_token):
    """
    Get spotify user's data via spotify API
    :param access_token:
    :return: Spotify API User Data
    """
    user_data = sf.get_user(access_token)
    return user_data


def get_random_song(artist):
    # Returns a random song from the user's top artist
    ...


def get_album_choices(albums_json, correct_album):
    # Returns a list of three albums, one of which is the album of 'song'
    # Eventually, we want the 2 other choices randomized
    # For now, just choose first 3 unique albums (including correct album)
    choices = [correct_album]
    wrong_choices = []
    # TODO assert albums_json has at least 3 albums
    assert len(albums_json['items']) > 3
    for album_dict in albums_json['items']:
        if [album_dict['name']] != correct_album:
            wrong_choices += [album_dict['name']]
    choices += wrong_choices[0:2]
    return choices


# Game
# Step 1, get the top artist of the user
# Step 2, pick a random song from an artist
# Step 3, pick 3 albums
# Step 4, let the user pick the right album
def guess_song_game(access_token):
    game_dict = {}
    top_artist_json = sf.get_top_artist_json(access_token)
    top_arist_id = top_artist_json['items'][0]['id']
    top_artist = top_artist_json['items'][0]['name']
    game_dict['artist'] = top_artist
    print(f"Top artist: {top_artist}")
    top_songs_json = sf.get_top_tracks_from_artist_json(access_token, top_arist_id)
    top_song = top_songs_json['tracks'][0]['name']
    game_dict['song'] = top_song
    print(f"Top song: {top_song}")
    correct_album = top_songs_json['tracks'][0]['album']['name']
    game_dict['correct_album'] = correct_album
    print(f"Top song's album: {correct_album}")
    # TODO, generate 3 album choices (including correct one)
    albums_json = sf.get_albums_from_artist_json(access_token, top_arist_id)
    choices = get_album_choices(albums_json, correct_album)
    game_dict['choices'] = choices
    print(f"{top_song} is from one of these albums: {choices}")
    return game_dict
