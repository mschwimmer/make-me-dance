import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = 'https://api.spotify.com/v1/'


# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-audio-features
# gets 1 track's data
def get_track_data(access_token, track_id):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    try:
        r = requests.get(BASE_URL + 'audio-features/' + track_id, headers=headers)
        r = r.json()
        return r
    except requests.exceptions.RequestException as e:
        return e


# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-several-audio-features
# gets max 100 tracks' data
def get_several_tracks_data(access_token, track_ids):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    payload = {'ids': track_ids}

    try:
        r = requests.get(BASE_URL + 'audio-features', headers=headers, params=payload)
        r = r.json()
        return r
    except requests.exceptions.RequestException as e:
        return e


# uses get_several_tracks_data for more than 100 tracks
# uses multithreading for speed
# returns [[{audio_feature dictionary}]]
def get_many_tracks_data(access_token, track_ids):
    total_tracks = len(track_ids)
    input_batches = []
    output_batches = []

    for i in range(0, total_tracks, 100):
        input_batches.append(",".join(track_ids[i:i + 100]))

    threads = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for batch in input_batches:
            threads.append(executor.submit(get_several_tracks_data, access_token, batch))
        for task in as_completed(threads):
            tracks_json = task.result()
            output_batches.append(tracks_json['audio_features'])

    return output_batches


# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlist
def get_data_from_href(access_token, href):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    try:
        r = requests.get(href, headers=headers)
        r = r.json()
        return r
    except requests.exceptions.RequestException as e:
        return e


# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlists-tracks
def get_playlist_items_from_playlist_id(access_token, playlist_id, offset=0, plist_name=None):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    payload = {'limit': 50, 'offset': offset}
    try:
        r = requests.get(BASE_URL + 'playlists/{id}/tracks'.format(id=playlist_id), headers=headers, params=payload)
        r = r.json()
        # adding a plist name field to make our lives easier in future
        if plist_name is not None:
            r['name'] = plist_name
        return r
    except requests.exceptions.RequestException as e:
        return e


# returns a dict that maps names of every track from a playlist to their track ID even if total_songs>50
def get_all_tracks_from_playlist_id(access_token, playlist_id, total_songs):
    track_names_to_id = {}
    offset = 0

    while offset < total_songs:
        tracks_json = get_playlist_items_from_playlist_id(access_token, playlist_id, offset=offset)
        for item in tracks_json['items']:
            name = item['track']['name']
            track_names_to_id[name] = item['track']['id']
        offset += 50

    return track_names_to_id


# we're going to try to implement multithreading here
# inputs: spotify API token, list of spotify track ids
# returns: the average danceability value for the given list of spotify track ids
def get_avg_danceability(token, tracks):
    dance_sum = 0
    total = len(tracks)
    input_batches = []
    output_batches = []

    # iterate through the total number of tracks by units of 100 to create batches of 100 comma separated track ids
    for i in range(0, total, 100):
        input_batches.append(",".join(tracks[i:i + 100]))

    threads = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for batch in input_batches:
            threads.append(executor.submit(get_several_tracks_data, token, batch))
        for task in as_completed(threads):
            tracks_json = task.result()
            output_batches.append(tracks_json)

    for batch in output_batches:
        for song in batch['audio_features']:
            dance_sum += song['danceability']

    avg = dance_sum / total
    return avg


def get_discography(access_token, artist_id):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    try:
        r = requests.get(BASE_URL + 'artists/' + artist_id + '/albums',
                         headers=headers,
                         params={'include_groups': 'album', 'limit': 50})
        d = r.json()
        return d
    except requests.exceptions.RequestException as e:
        return e


# returns all tracks from an artist
def get_all_artist_tracks(access_token):
    data = []  # will hold all track info
    albums = []  # to keep track of duplicates
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }
    artist_id = '4V8LLVI7PbaPR0K2TGSxFF'
    try:
        d = get_discography(access_token, artist_id)

        # loop over albums and get all tracks
        for album in d['items']:
            album_name = album['name']

            trim_name = album_name.split('(')[0].strip()
            # skip if a duplicate
            if trim_name.upper() in albums:
                continue
            albums.append(trim_name.upper())

            print(album_name)

            # pull all tracks from this album
            r = requests.get(BASE_URL + 'albums/' + album['id'] + '/tracks',
                             headers=headers)
            tracks = r.json()['items']

            for track in tracks:
                f = requests.get(BASE_URL + 'audio-features/' + track['id'],
                                 headers=headers)
                f = f.json()

                # combine with album info
                f.update({
                    'track_name': track['name'],
                    'album_name': album_name,
                    'short_album_name': trim_name,
                    'release_date': album['release_date'],
                    'album_id': album['id']
                })

                data.append(f)
        return data
    except requests.exceptions.RequestException as e:
        return e


# returns max 50 playlists from user, default is 20
def get_user_playlists(access_token, user_id):
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    try:
        r = requests.get(BASE_URL + 'users/' + '{user_id}'.format(user_id=user_id) + '/playlists', headers=headers)
        r = r.json()
        return r
    except requests.exceptions.RequestException as e:
        return e
