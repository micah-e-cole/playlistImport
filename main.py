import os
import urllib.parse
import pandas as pd
from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# ─── Load Environment Variables ────────────────────────────────
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SCOPE = "playlist-read-private playlist-read-collaborative"

if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
    raise SystemExit("❌ Missing Spotify credentials. Check your .env file.")

print("✅ Environment loaded. Using app credentials:")
print(f"  Client ID: {CLIENT_ID[:6]}... (hidden)")
print(f"  Redirect URI: {REDIRECT_URI}")

# ─── Qobuz Search Link Helper ─────────────────────────────────
def generate_qobuz_link(track_name, artist_name):
    query = urllib.parse.quote_plus(f"{artist_name} {track_name}")
    return f"https://www.qobuz.com/us-en/search?q={query}"

# ─── Spotify Auth Wrapper for Multiple Users ──────────────────
def get_spotify_for_user(cache_name):
    """Authenticate each user and save token to a local JSON file."""
    auth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_path=cache_name,
        show_dialog=True,  # forces Spotify to ask for login once per user
        open_browser=True
    )
    return Spotify(auth_manager=auth)

# ─── Export Function ───────────────────────────────────────────
def export_playlists_for_user(sp, username):
    """Fetch playlists for one authenticated user."""
    user = sp.current_user()
    print(f"\n🎧 Exporting playlists for {user['display_name']} ({username})")

    playlists = sp.current_user_playlists()
    tracks_data = []

    for playlist in playlists["items"]:
        playlist_name = playlist["name"]
        playlist_id = playlist["id"]
        print(f"  → Fetching tracks from playlist: {playlist_name}")

        results = sp.playlist_tracks(playlist_id)
        while results:
            for item in results["items"]:
                track = item["track"]
                if not track:
                    continue
                track_name = track["name"]
                artist_name = track["artists"][0]["name"]
                album_name = track["album"]["name"]
                qobuz_link = generate_qobuz_link(track_name, artist_name)
                tracks_data.append({
                    "User": username,
                    "Playlist": playlist_name,
                    "Track": track_name,
                    "Artist": artist_name,
                    "Album": album_name,
                    "Qobuz_Search_Link": qobuz_link
                })
            results = sp.next(results) if results["next"] else None

    return tracks_data

# ─── Run for All Family Members ────────────────────────────────
def export_all_users():
    # List each family member once; each gets their own token file
    users = {
        "micah": "micah_token.json",
        "partner": "clare_token.json"
    }

    all_tracks = []

    for username, cache_file in users.items():
        print(f"\n🔑 Logging in for: {username}")
        sp = get_spotify_for_user(cache_file)
        user_tracks = export_playlists_for_user(sp, username)
        all_tracks.extend(user_tracks)

    # Save everything to one CSV
    df = pd.DataFrame(all_tracks)
    output_file = "all_family_spotify_playlists.csv"
    df.to_csv(output_file, index=False, encoding="utf-8")
    print(f"\n✅ Export complete! Saved as: {output_file}")

# ─── Run Script ───────────────────────────────────────────────
if __name__ == "__main__":
    export_all_users()
