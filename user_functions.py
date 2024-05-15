import collections
import json
import time
import pandas as pd
import spotify_functions as sf
from itertools import chain
from concurrent.futures import ThreadPoolExecutor, as_completed


def timer(func):
    def wrapper(*args, **kwargs):
        t = time.time()
        res = func(*args, **kwargs)
        time_past = time.time() - t
        print(f"{func.__name__} took {int(time_past / 60)} minutes, {time_past % 60} seconds")
        return res
    return wrapper


@timer
def get_user_data(access_token):
    """
    Get spotify user's data via spotify API
    :param access_token:
    :return: Spotify API User Data JSON
    """
    user_data = sf.get_user(access_token)
    return user_data


@timer
def get_user_playlists(access_token):
    """
    Get spotify user's playlist data via spotify API
    :param access_token:
    :return: User's playlist JSON
    """
    playlist_data = sf.get_current_user_playlists(access_token)
    print(f"Found {len(playlist_data['items'])} playlists for user")
    return playlist_data


@timer
def get_all_playlist_items(access_token, playlists):
    for playlist in playlists:
        playlist['playlist_items'] = []

    # Threadpool to handle concurrent requests
    with ThreadPoolExecutor(max_workers=20) as executor:
        task_to_playlist = {}
        for playlist in playlists:
            offset = 0
            while offset < playlist['track_total']:
                task = executor.submit(sf.get_playlist_items_from_playlist_id, access_token, playlist['playlist_id'], offset)
                task_to_playlist[task] = playlist
                offset += 50

        for task in as_completed(task_to_playlist):
            playlist = task_to_playlist[task]
            try:
                result = task.result()
                playlist['playlist_items'].append(result)
            except Exception as e:
                print(f"Error retrieving data for playlist {playlist['playlist_name']}: {e} ")

    return playlists


@timer
def get_many_tracks_data(access_token, song_ids):
    print(f"Getting {len(song_ids)} songs' data")
    return sf.get_many_tracks_data(access_token, song_ids)


@timer
def get_user_songs(access_token, playlists_data):
    if playlists_data is None:
        raise ValueError("Playlists data can't be None")
    print(f"Gathering all songs from user's playlists")

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

    # Process each playlists tracks
    songs = {}
    playlists = get_all_playlist_items(access_token, playlists)
    for playlist in playlists:
        if not playlist or 'playlist_items' not in playlist:
            continue
        for playlist_item in playlist['playlist_items']:
            for item in playlist_item['items']:
                try:
                    if item['track']['id'] and item['track']['id'] not in songs:
                        song = {'track_name': item['track']['name'],
                                'track_id': item['track']['id'],
                                'track_album': item['track']['album']['name'],
                                'track_artist': item['track']['artists'][0]['name'],
                                'playlist_name': playlist['playlist_name']}
                        songs[item['track']['id']] = song

                except KeyError as e:
                    print(f"KeyError while parsing through playlist item data: {e}")

    # Retrieve details track data
    unique_track_data = get_many_tracks_data(access_token, list(songs.keys()))
    flat_track_data = list(chain.from_iterable(unique_track_data))
    flat_track_data = [track for track in flat_track_data if track is not None]
    # Remove Nulls from list
    for track_data in flat_track_data:
        if track_data['id'] in songs:
            songs[track_data['id']]['danceability'] = track_data['danceability']
    song_df = pd.DataFrame.from_dict(songs, orient='index')
    song_df = song_df[~song_df['track_name'].duplicated()]
    dance_df = song_df.sort_values('danceability', ascending=False).iloc[0:30]

    dance_df.reset_index(drop=True, inplace=True)
    return dance_df


def create_playlist(access_token, user_id, playlist_name):
    playlist_response = sf.create_playlist_for_user(access_token, user_id, playlist_name)
    return playlist_response


def add_tracks_to_playlist(access_token, playlist_id, track_uris):
    add_tracks_response = sf.add_tracks_to_playlist(access_token, playlist_id, track_uris)
    return add_tracks_response
