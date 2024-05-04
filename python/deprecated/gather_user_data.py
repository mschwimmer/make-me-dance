"""
NO LONGER USED
"""
import time
import pandas as pd
import spotify_functions as sp
from itertools import chain
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_user_songs(access_token):
    print(f"Gathering all songs from user's playlists")
    full_start = time.time()

    # returns json of the users playlists via the spotify API
    user_playlists = sp.get_current_user_playlists(access_token)

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
                threads.append(executor.submit(sp.get_playlist_items_from_playlist_id, access_token, plist_id, offset, plist_name))
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
    unique_track_data = sp.get_many_tracks_data(access_token, unique_ids)
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
