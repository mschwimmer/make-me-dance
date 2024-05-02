import time
import pandas as pd
import spotify_functions as sf
from itertools import chain
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_user_data(access_token):
    """
    Get spotify user's data via spotify API
    :param access_token:
    :return: Spotify API User Data JSON
    """
    user_data = sf.get_user(access_token)
    return user_data


def get_user_playlists(access_token):
    """
    Get spotify user's playlist data via spotify API
    :param access_token:
    :return: User's playlist JSON
    """
    playlist_data = sf.get_current_user_playlists(access_token)
    print(f"Found {len(playlist_data['items'])} playlists for user")
    return playlist_data


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

def get_user_top_artist(access_token):
    top_artist_json = sf.get_top_artist_json(access_token)
    return top_artist_json['items'][0]['name']

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


def get_user_songs(access_token):
    print(f"Gathering all songs from user's playlists")
    full_start = time.time()

    # returns json of the users playlists via the spotify API
    user_playlists = sf.get_current_user_playlists(access_token)

    # list of all playlist hrefs ['user plist1 href', 'user plist2 href'...]
    playlist_hrefs = []
    # list of playlist names ['user plist1 name', 'user plist2 name',...]
    plist_names = []
    # list of playlists' spotify ids ['user plist1 id', 'user plist2 id',...]
    plist_ids = []
    # list of track totals
    track_totals = []

    start = time.time()
    # loop to populate plist_name, playlist_hrefs, and plist_id
    for item in user_playlists['items']:
        plist_names.append(item['name'])
        plist_ids.append(item['id'])
        track_totals.append(item['tracks']['total'])
        playlist_hrefs.append(item['href'])
    end = time.time()
    time_past = end - start
    print("Collecting playlist ID, Name, and Href took:", int(time_past/60), "minutes", time_past % 60, "seconds")

    # a song_unit is a list containing
    # ["track name", "track id", "playlist"]
    # list that contains every song unit [[name,id,plist]]
    song_units = []

    start = time.time()
    threads = []
    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for plist_name, plist_id, total in zip(plist_names, plist_ids, track_totals):
            offset = 0
            while offset < total:
                threads.append(executor.submit(sf.get_playlist_items_from_playlist_id, access_token, plist_id, offset, plist_name))
                offset += 50
        for task in as_completed(threads):
            result = task.result()
            results.append(task.result())

    for result in results:
        for item in result['items']:
            if item['track']['id'] is not None:
                song_units.append([item['track']['name'], item['track']['id'], result['name']])
    end = time.time()
    time_past = end - start
    print("Collecting all song units via get_playlist_items_from_playlist_id:", int(time_past / 60), "minutes", time_past % 60, "seconds")

    song_df = pd.DataFrame(song_units, columns=['track_name', 'track_id', 'plist_name'])
    all_track_ids = song_df['track_id'].to_list()

    unique_ids = list(set(all_track_ids))
    # unique_ids = [item for item in all_track_ids if all_track_ids.count(item) == 1]
    start = time.time()
    unique_track_data = sf.get_many_tracks_data(access_token, unique_ids)
    end = time.time()
    time_past = end - start
    print("Collecting all unique songs' track data via get_many_tracks_data took:", int(time_past/60), "minutes", time_past % 60, "seconds")

    flat_track_data = list(chain.from_iterable(unique_track_data))
    flat_df = pd.DataFrame(flat_track_data)
    print("flat_df\n", flat_df)
    flat_df.rename(columns={'id': 'track_id'}, inplace=True)
    # Set indexes to track_id for joining data to song_df
    flat_df.set_index('track_id', drop=True, inplace=True)
    song_df.set_index('track_id', drop=True, inplace=True)
    song_df = song_df.join(flat_df)
    song_df = song_df[~song_df.index.duplicated()]
    song_df.reset_index(inplace=True)

    full_end = time.time()
    full_time = full_end - full_start
    print("Gathering user's songs took", int(full_time/60), "minutes", full_time % 60, "seconds")
    # pretty = json.dumps(playlist_to_track_dict, indent=4)
    return song_df


def get_top_dance_songs(song_df, num_songs):
    return song_df.sort_values('danceability', ascending=False).iloc[0:num_songs]
