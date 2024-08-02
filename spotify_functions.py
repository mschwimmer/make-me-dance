import json

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = 'https://api.spotify.com/v1/'


# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-several-audio-features
# Returns max 100 tracks' data
def get_several_tracks(access_token: str, track_ids: list[str]) -> dict:
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    payload = {'ids': track_ids}

    try:
        response = requests.get(BASE_URL + 'audio-features', headers=headers, params=payload)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')
        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


# Uses get_several_tracks_data & multiprocessing for more than 100 tracks
# Returns [[{audio_feature dictionary}]]
def get_many_tracks_data(access_token: str, track_ids: list[str]) -> list:
    total_tracks = len(track_ids)
    track_id_batches = []
    output_batches = []

    for i in range(0, total_tracks, 100):
        track_id_batches.append(",".join(track_ids[i:i + 100]))

    threads = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        for track_id_batch in track_id_batches:
            threads.append(executor.submit(get_several_tracks, access_token, track_id_batch))
        for task in as_completed(threads):
            tracks_json = task.result()
            output_batches.append(tracks_json['audio_features'])

    return output_batches


# https://developer.spotify.com/documentation/web-api/reference/#/operations/get-playlists-tracks
def get_playlist_items_from_playlist_id(access_token: str, playlist_id: str, offset: int = 0) -> dict:
    headers = {
        'Authorization': 'Bearer {token}'.format(token=access_token)
    }

    payload = {'fields': "items(track(id,name,album(name),artists(name)))",
               'limit': 50,
               'offset': offset}
    try:
        response = requests.get(BASE_URL + 'playlists/{id}/tracks'.format(id=playlist_id), headers=headers, params=payload)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')
        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


# returns user profile
def get_user(access_token: str) -> dict:
    # set up headers with authorization using access token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    try:
        # send request to user endpoint
        response = requests.get("https://api.spotify.com/v1/me", headers=headers)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')

        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


# returns CURRENT USER's playlists
def get_current_user_playlists(access_token: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # set up parameters for top artists endpoint
    params = {
        "limit": 25,
    }

    try:
        # send request to user endpoint
        response = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers, params=params)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')

        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


def get_top_artist_json(access_token: str) -> dict:
    # set up headers with authorization using access token
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # set up parameters for top artists endpoint
    params = {
        "time_range": "long_term",
        "limit": 1,
    }

    try:
        # send request to top artists endpoint
        # response = requests.get(BASE_URL + 'users/' + user_id + '/top/artists', headers=headers, params=params)
        response = requests.get("https://api.spotify.com/v1/me/top/artists", headers=headers, params=params)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')

        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


def get_top_tracks_from_artist_json(access_token: str, artist_id: str) -> dict:
    # set up headers with authorization using access token
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    params = {
        "market": "US"
    }
    try:
        response = requests.get(f"{BASE_URL}artists/{artist_id}/top-tracks", headers=headers, params=params)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')

        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


def get_albums_from_artist_json(access_token: str, artist_id: str) -> dict:
    # set up headers with authorization using access token
    headers = {
        "Authorization": f"Bearer {access_token}",
    }
    params = {
        'include_groups': 'album',
        "market": "US"
    }
    try:
        response = requests.get(f"{BASE_URL}artists/{artist_id}/albums", headers=headers, params=params)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')

        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


# https://developer.spotify.com/documentation/web-api/reference/create-playlist
def create_playlist_for_user(access_token: str, user_id: str, playlist_name: str) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    # set up parameters for playlist name
    data = {
        "name": playlist_name,
        "description": "My top dance songs ;)",
        "public": False
    }

    try:
        # send request to user endpoint
        response = requests.post(f"https://api.spotify.com/v1/users/{user_id}/playlists", headers=headers, json=data)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')

        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)


# https://developer.spotify.com/documentation/web-api/reference/add-tracks-to-playlist
def add_tracks_to_playlist(access_token: str, playlist_id: str, track_uris: list) -> dict:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    # set up parameters for playlist name
    data = {
        "uris": track_uris
    }

    try:
        # send request to user endpoint
        response = requests.post(f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks", headers=headers,
                                 json=data)
        response.raise_for_status()
        response = response.json()
        if response is None:
            raise ValueError('API returned null object')

        return response
    except json.JSONDecodeError as decode_err:
        print(f"JSON decode error: {decode_err}")
    except requests.exceptions.RequestException as e:
        print(e)
