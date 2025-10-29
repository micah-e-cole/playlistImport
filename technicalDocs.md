# Playlist Importer Technical Implementation Plan

Project: Spotify → Qobuz Playlist Importer

Goal: Automatically copy user playlists from Spotify into Qobuz, preserving track order and metadata as accurately as possible.

## 1. System Overview

The importer acts as a middleware bridge between Spotify and Qobuz. It uses their respective APIs to:

- Authenticate user accounts.
- Retrieve playlists and track metadata from Spotify.
- Search for matching tracks on Qobuz.
- Create and populate playlists on Qobuz.

You’ll implement this as a command-line tool or small web app, depending on how you want to interact with it.

## 2. Architecture Design

### Components

| Component | Purpose |
| --- | --- |
|Auth Module | Handles Spotify OAuth2 and Qobuz session authentication |
| Spotify Client | Fetches playlists, tracks, and metadata via Spotify’s REST AP |
| Matching Engine | Maps Spotify tracks to Qobuz equivalents using metadata search |
| Qobuz Client | Creates and populates playlists on Qobuz |
| CLI/UI Layer | Provides user interaction (e.g., select playlists, show progress) |
| Persistence Layer (optional) | Stores results of previous matches for caching or auditing |

### Data Flow

``` [User] → [Spotify OAuth] → [Fetch Playlists] → [Track Metadata]
                 ↓
        [Search Matches on Qobuz]
                 ↓
         [Create Qobuz Playlist]
                 ↓
           [Add Tracks to Qobuz]
```

## 3. Authentication

### Spotify

- API Base: https://api.spotify.com/v1
- Auth Flow: OAuth 2.0 Authorization Code Grant.
- Libraries: [spotipy](https://spotipy.readthedocs.io/en/2.25.1/) simplifies this

Scopes required:

- playlist-read-private
- playlist-read-collaborative
- Tokens: You’ll receive an access_token (valid ~1 hour) and refresh_token for long sessions

### Qobuz

- API Base: https://www.qobuz.com/api.json/0.2/
- Auth Flow: API key + user credentials.

Steps:

- Obtain an App ID from Qobuz Developer portal.
- Log in via /user/login using email, password, and app_id.
- Receive user_auth_token — this authorizes all playlist operations

**Purpose:** These steps establish secure communication with each service. Spotify ensures access via OAuth consent; Qobuz uses a direct login method since it lacks a public OAuth flow.

## 4. Spotify Playlist Retrieval

### Endpoints

- ```GET /me/playlists``` — Lists user playlists
- ```GET /playlists/{playlist_id}/tracks``` — Retrieves tracks

### Implementation

Use ```spotipy``` or direct ```requests``` calls:

```playlists = sp.current_user_playlists()
for playlist in playlists['items']:
    print(playlist['name'], playlist['id'])```

Each track object returned includes metadata like:

```{
  "name": "Track Title",
  "artists": [{"name": "Artist Name"}],
  "album": {"name": "Album Title"},
  "duration_ms": 180000,
  "external_urls": {"spotify": "https://open.spotify.com/track/..."}
}
```

**Purpose:** This step builds a complete list of songs you’ll attempt to migrate. The metadata provides the search keys you’ll need to find matches on Qobuz.

## 5. Matching Engine

The matching engine searches Qobuz for each Spotify track.

### Input

- Spotify track name
- First artist name
- Optional: album name, duration

### Qobuz Search Endpoint

```GET https://www.qobuz.com/api.json/0.2/track/search
    ?query=<song+artist>&limit=1&app_id=<QOBUZ_APP_ID>
```

### Matching Logic

1. Construct a search string like "{track_name} {artist}".

2. Normalize text:

    - Lowercase
    - Remove accents/punctuation
    - Strip special characters (e.g., “(Remastered)”)

3. Compare best result by:

    - Exact title match
    - Fuzzy ratio (use fuzzywuzzy or rapidfuzz)
    - Optional duration check (±5 seconds tolerance)

#### Example

```def find_qobuz_track(spotify_track, qobuz_session):
    query = f"{spotify_track['name']} {spotify_track['artists'][0]['name']}"
    r = qobuz_session.get(
        "https://www.qobuz.com/api.json/0.2/track/search",
        params={"query": query, "limit": 3, "app_id": QOBUZ_APP_ID}
    )
    items = r.json().get("tracks", {}).get("items", [])
    return items[0] if items else None
```

**Purpose:** This layer maps the Spotify song to its closest Qobuz equivalent using textual and optional duration matching.

## 6. Qobuz Playlist Creation

### Endpoint

```GET /playlist/create
    ?name=<playlist_name>
    &app_id=<QOBUZ_APP_ID>
    &user_auth_token=<USER_AUTH_TOKEN>
```

#### Response returns

```{"id": "987654321", "name": "My Imported Playlist"}```

**Purpose**
Creates a new Qobuz playlist container where tracks will be inserted.

## 7. Adding tracks to Qobuz Playlist

### Endpoint

```GET /playlist/addTracks
    ?playlist_id=<playlist_id>
    &track_ids=<comma-separated-list>
    &app_id=<QOBUZ_APP_ID>
    &user_auth_token=<USER_AUTH_TOKEN>
```

Batch tracks in groups (e.g., 50 per request) to reduce API calls.

**Purpose:** This uploads all the found Qobuz track IDs to the new playlist in the original Spotify order.

## 8. Logging & Error Handling

- Maintain a CSV report:
  - Columns: Spotify Track, Qobuz Match, Match Confidence, Status.
- Retry on transient errors (HTTP 429, 500).
- Respect Spotify rate limits (Retry-After header).

Count successful vs. failed matches.

#### Example:

```import csv

with open("unmatched_tracks.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["Spotify Track", "Artist"])
    for t in failed_matches:
        writer.writerow([t['name'], t['artists'][0]['name']])
```

**Purpose:** Ensures visibility into what succeeded or failed and enables incremental reruns.

## 9. CLI / UI Layer

A **CLI** is easiest for first implementation.

Example options:

```python importer.py --playlist "Driving Jams"
python importer.py --all
```

Features:

- List available Spotify playlists.
- Allow selection by name or ID.
- Show progress with tqdm.
- Confirm before writing to Qobuz.

Optionally later:

- Add a Flask, tkinter, or Streamlit web front-end for user login and playlist selection.

## 10. Environment & Configuration

Using a ```.env``` (e.g. ini) file

```SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://localhost:8080
QOBUZ_APP_ID=...
QOBUZ_USER=email@example.com
QOBUZ_PASS=supersecret
```

Ensure the ```requirements.txt``` includes:

```spotipy
requests
python-dotenv
tqdm
rapidfuzz
```

**Purpose:** Keeps secrets out of code and makes the app portable across machines.

