import time
import pandas as pd
import config
import spotify_functions as sp
from itertools import chain
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

CLIENT_ID = config.CLIENT_ID
CLIENT_SECRET = config.CLIENT_SECRET
token = config.get_token()
user_id = config.user_id


# this function takes in a spotify playlist href
# this is an old obsolete function that I should prob delete
def get_song_units(playlist_href):
    plist_json = sp.get_data_from_href(token, playlist_href)
    song_units = []
    # for a playlist >50 songs, href_json['tracks']['next'] represents following tracks within playlist
    next_track_link = plist_json['tracks']['next']
    plist_name = plist_json['name']
    for item in plist_json['tracks']['items']:
        name = item['track']['name']
        if item['track']['id'] is not None:
            song_id = item['track']['id']
            song_units.append([name, song_id, plist_name])

    while next_track_link is not None:
        next_json = sp.get_data_from_href(token, next_track_link)
        next_track_link = next_json['next']
        for item in next_json['items']:
            if item['track']['id'] is not None:
                name = item['track']['name']
                song_id = item['track']['name']
                song_units.append([name, song_id, plist_name])

    return song_units

def main_runner():
    full_start = time.time()

    # returns json of the users playlists via the spotify API
    # TODO remember this only returns 20, eventually need to return all playlists
    user_playlists = sp.get_user_playlists(token, user_id)

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
                threads.append(executor.submit(sp.get_playlist_items_from_playlist_id, token, plist_id, offset, plist_name))
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

    gold_df = pd.DataFrame(song_units, columns=['track_name', 'track_id', 'plist_name'])
    all_track_ids = gold_df['track_id'].to_list()

    unique_ids = list(set(all_track_ids))
    #unique_ids = [item for item in all_track_ids if all_track_ids.count(item) == 1]
    start = time.time()
    unique_track_data = sp.get_many_tracks_data(token, unique_ids)
    end = time.time()
    time_past = end - start
    print("Collecting all unique songs' track data via get_many_tracks_data took:", int(time_past/60), "minutes", time_past % 60, "seconds")

    flat_track_data = list(chain.from_iterable(unique_track_data))
    flat_df = pd.DataFrame(flat_track_data)
    print("flat_df\n", flat_df)
    flat_df.rename(columns={'id': 'track_id'}, inplace=True)
    #flat_df.set_index('track_id', drop=False, inplace=True)
    gold_df = gold_df.join(flat_df.set_index('track_id'), on='track_id')

    #USE df.groupby(PLAYLIST NAME).median HAHA HO SHIt WE GOT THIS FROM WORK
    gold_copy = gold_df.groupby('plist_name').mean()
    print("test_copy \n", gold_copy)

    new_plist_to_avg_dance = dict(zip(gold_copy.index.values.tolist(), gold_copy['danceability'].to_list()))
    for i in plist_names:
        print(i, "groupyby().mean() method we got", new_plist_to_avg_dance[i])
        print("-------")

    full_end = time.time()
    full_time = full_end - full_start
    print("full script took", int(full_time/60), "minutes", full_time % 60, "seconds")
    # pretty = json.dumps(playlist_to_track_dict, indent=4)

if __name__ == '__main__':
    main_runner()