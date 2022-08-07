from dotenv import load_dotenv, find_dotenv
import requests
import base64
import json
import os

load_dotenv(find_dotenv())
REFRESH_TOKEN = os.environ.get("REFRESH_TOKEN").strip()
CLIENT_ID = os.environ.get("CLIENT_ID").strip()
CLIENT_SECRET = os.environ.get("CLIENT_SECRET").strip()
RELEASE_RADAR_ID = os.environ.get("RELEASE_RADAR_ID").strip()
SAVE_TO_ID = os.environ.get("SAVE_TO_ID").strip()

OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"
def refresh_access_token():
    payload = {
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
    }
    encoded_client = base64.b64encode((CLIENT_ID + ":" + CLIENT_SECRET).encode('ascii'))
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic %s" % encoded_client.decode('ascii')
    }
    response = requests.post(OAUTH_TOKEN_URL, data=payload, headers=headers)
    return response.json()


def get_playlist(access_token, playlist_id):
    url = "https://api.spotify.com/v1/playlists/%s" % playlist_id 
    headers = {
       "Content-Type": "application/json",
       "Authorization": "Bearer %s" % access_token
    }
    response = requests.get(url, headers=headers)
    return response.json()

def add_to_playlist(access_token, tracklist):
    url = "https://api.spotify.com/v1/playlists/%s/tracks" % SAVE_TO_ID
    payload = {
        "uris" : tracklist
    }
    headers = {
       "Content-Type": "application/json",
       "Authorization": "Bearer %s" % access_token
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    return response.json()

def get_all_playlist_tracks(access_token, playlist_id):
    tracks = []

    url = "https://api.spotify.com/v1/playlists/%s/tracks" % playlist_id
    while url != None:
        payload = {
            "limit": 10,
            "offset": 0
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % access_token
        }
        response = requests.get(url, params=payload, headers=headers) 
        # print(response)

        data = response.json()
        url = data["next"]
        tracks += data["items"]
    
    return tracks

def check_saves(access_token, tracks):
    saved_tracks = []
    # print(tracks[0])
    while len(tracks) > 0:
        group = tracks[0:50]
        # print(len(group))
        tracks = tracks[50:]

        track_ids = ','.join([str(i["track"]["id"]) for i in group])

        # print(track_ids)

        url = "https://api.spotify.com/v1/me/tracks/contains"
        payload = {
            "ids": track_ids
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % access_token
        }
        response = requests.get(url, params=payload, headers=headers) 
        data = response.json()
        # print(data)

        for i, x in enumerate(data):
            if(x):
                saved_tracks.append(group[i])
    return saved_tracks

def remove_tracks_from_playlist(access_token, playlist_id, tracks):
    output = {}
    num_deleted = 0

    while len(tracks) > 0:
        group = tracks[0:100]
        tracks = tracks[100:]

        payload = {
            "tracks": []
        }

        for track in group:
            # print("TRACK")
            payload["tracks"].append({"uri": track["track"]["uri"]})
            num_deleted = num_deleted + 1
        
        # print(payload)

        url = "https://api.spotify.com/v1/playlists/%s/tracks" % playlist_id
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % access_token
        }
        response = requests.delete(url, json=payload, headers=headers) 
        data = response.json()
        output = data
    return output, num_deleted

# remove saved songs from SAVE_TO_ID playlist
def remove_saved(access_token):

    # get all songs in SAVE_TO_ID playlist
    tracks = get_all_playlist_tracks(access_token, SAVE_TO_ID)
    
    # check which tracks from above are saved
    saved_tracks = check_saves(access_token, tracks)

    # remove saved tracks from playlist
    response, num_removed = remove_tracks_from_playlist(access_token, SAVE_TO_ID, saved_tracks)

    # check if we did anything
    if "snapshot_id" in response:
        print(f"Successfully removed {num_removed} already saved songs")
    else:
        print(response)
    


def main():
    if REFRESH_TOKEN is None or CLIENT_ID is None or CLIENT_SECRET is None or RELEASE_RADAR_ID is None or SAVE_TO_ID is None:
        print("Environment variables have not been loaded!")
        return

    access_token = refresh_access_token()['access_token']

    # add release radar songs to discovery queue
    tracks =  get_playlist(access_token, RELEASE_RADAR_ID)['tracks']['items']
    tracklist = []
    for item in tracks:
        tracklist.append(item['track']['uri'])
    response = add_to_playlist(access_token, tracklist)

    if "snapshot_id" in response:
        print("Successfully added all Release Radar songs")
    else:
        print(response)

    # remove saved songs from discovery queue
    response = remove_saved(access_token)


main()