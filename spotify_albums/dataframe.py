import pandas as pd
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from .markdown import load_markdown_albums
from .spotify_api import fetch_album_details


def build_dataframe(listened_path):
    albums = load_markdown_albums(listened_path)
    spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())

    rows = []
    for (artist, album_name), url in albums:
        print(f"Fetching: {artist} - {album_name}")
        year, duration_min, genres = fetch_album_details(spotify, url)
        rows.append({
            'artist': artist,
            'album': album_name,
            'year': year,
            'duration_min': duration_min,
            'genres': genres,
            'url': url,
        })

    return pd.DataFrame(rows)
