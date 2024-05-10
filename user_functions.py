import json
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


def get_user_songs(access_token):
    print(f"Gathering all songs from user's playlists")
    full_start = time.time()

    # Attempt to get users playlists from spotify API
    try:
        user_playlists = sf.get_current_user_playlists(access_token)
    except (json.JSONDecodeError, TypeError, KeyError) as e:
        print(f"Error decoding playlist: {e}")
        return pd.DataFrame()  # Return empty dataframe on error

    # Initialize empty lists for playlist details
    playlist_hrefs = []
    plist_names = []
    plist_ids = []
    track_totals = []

    # Safeguard against bad data
    items = user_playlists.get("items", [])
    if not items:
        print("No playlists found or malformed response.")
        return pd.DataFrame()

    # Extract playlist data
    start = time.time()
    for item in items:
        try:
            plist_names.append(item['name'])
            plist_ids.append(item['id'])
            track_totals.append(item['tracks']['total'])
            playlist_hrefs.append(item['href'])
        except KeyError as e:
            print(f"KeyError while extracting playlist data {e}")
    end = time.time()
    time_past = end - start
    print(f"Collecting playlist ID, Name, and Href took: {int(time_past / 60)} minutes, {time_past % 60} seconds")

    # List to hold all song units
    song_units = []
    start = time.time()
    threads = []
    results = []

    # Threadpool to handle concurrent requests
    with ThreadPoolExecutor(max_workers=20) as executor:
        for plist_name, plist_id, total in zip(plist_names, plist_ids, track_totals):
            offset = 0
            while offset < total:
                threads.append(
                    executor.submit(sf.get_playlist_items_from_playlist_id, access_token, plist_id, offset, plist_name))
                offset += 50
        for task in as_completed(threads):
            try:
                result = task.result()
                results.append(result)
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error processing playlist items: {e}")

    # Process each playlist's tracks
    for result in results:
        if not result or 'items' not in result:
            continue  # Skip bad results
        for item in result['items']:
            try:
                if item['track']['id'] is not None:
                    song_units.append([item['track']['name'],
                                       item['track']['id'],
                                       item['track']['album']['name'],
                                       item['track']['artists'][0]['name'],
                                       result['name']])
            except KeyError as e:
                print(f"KeyError while extracting song data: {e}")

    end = time.time()
    time_past = end - start
    print(f"Collecting all song units via get_playlist_items_from_playlist_id: {int(time_past / 60)} minutes, {time_past % 60} seconds")

    # Process and merge song data
    song_df = pd.DataFrame(song_units, columns=['track_name', 'track_id', 'album', 'artist', 'plist_name'])
    all_track_ids = song_df['track_id'].to_list()
    unique_ids = list(set(all_track_ids))

    # Retrieve details track data
    try:
        start = time.time()
        unique_track_data = sf.get_many_tracks_data(access_token, unique_ids)
        end = time.time()
        time_past = end - start
        print("Collecting all unique songs' track data via get_many_tracks_data took:", int(time_past / 60), "minutes",
              time_past % 60, "seconds")

        flat_track_data = list(chain.from_iterable(unique_track_data))
        flat_df = pd.DataFrame(flat_track_data)
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error while collection track data: {e}")
        return pd.DataFrame()

    flat_df.rename(columns={'id': 'track_id'}, inplace=True)
    flat_df.set_index('track_id', drop=True, inplace=True)
    song_df.set_index('track_id', drop=True, inplace=True)
    song_df = song_df.join(flat_df)
    song_df = song_df[~song_df.index.duplicated()]
    song_df.reset_index(inplace=True)

    full_end = time.time()
    full_time = full_end - full_start
    print(f"Gathering user's songs took:  {int(time_past / 60)} minutes, {time_past % 60} second")
    return song_df


def create_playlist(access_token, user_id, playlist_name):
    playlist_response = sf.create_playlist_for_user(access_token, user_id, playlist_name)
    return playlist_response


def add_tracks_to_playlist(access_token, playlist_id, track_uris):
    add_tracks_response = sf.add_tracks_to_playlist(access_token, playlist_id, track_uris)
    return add_tracks_response
