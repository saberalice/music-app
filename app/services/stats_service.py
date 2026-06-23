"""聽歌統計的商業邏輯。

兩部分:
1. 純彙總函式 compute_*:輸入 Python 資料、輸出統計結果,不碰 DB/網路,
   單元測試最好寫(見 tests/test_stats.py)。
2. 編排函式:把 client(抓資料)、repository(存取)、純函式(彙總)串起來,
   給 router 呼叫。router 只認得這層,不直接碰 repository。
"""

import json
from collections import Counter
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.schemas import GenreCount, TopArtistOut
from app.repositories.music_repository import MusicRepository
from app.services.lastfm_client import LastfmClient
from app.services.spotify_client import SpotifyClient


# --- 純彙總函式 ---
def compute_genre_distribution(
    genres_lists: list[list[str]], min_count: int = 1
) -> list[GenreCount]:
    """把每位歌手的曲風攤平統計,依次數由多到少排序。

    min_count:只回傳出現次數 >= 此值的曲風,用來砍掉只出現一次的長尾雜訊。
    """
    counter: Counter[str] = Counter()
    for genres in genres_lists:
        counter.update(genres)
    return [
        GenreCount(genre=g, count=c)
        for g, c in counter.most_common()
        if c >= min_count
    ]


def compute_heatmap(timestamps: list[datetime]) -> list[list[int]]:
    """產生 7×24 的聽歌熱力圖(星期一=0 … 星期日=6;小時 0–23)。

    注意:時間是 UTC,熱力圖也是 UTC 時段。要顯示本地時間之後可再轉換。
    """
    grid = [[0] * 24 for _ in range(7)]
    for ts in timestamps:
        grid[ts.weekday()][ts.hour] += 1
    return grid


# --- 編排(給 router 用)---
def sync_from_spotify(session: Session) -> dict:
    """從 Spotify 抓 Top Artists / Tracks / 最近播放,寫進 DB。

    曲風(genres)Spotify 新 app 拿不到,改用 Last.fm 逐位歌手補上
    (沒設 LASTFM_API_KEY 時就維持空的)。
    """
    spotify = SpotifyClient()
    lastfm = LastfmClient(settings.lastfm_api_key)
    repo = MusicRepository(session)

    artists = spotify.fetch_top_artists()
    # 用 Last.fm 補曲風(這一步就是 Day 8 多來源整合的雛形:
    # 同一個 ArtistDTO,資料來自兩個不同來源)
    for artist in artists:
        artist.genres = lastfm.fetch_genres(artist.name)

    tracks = spotify.fetch_top_tracks()
    plays = spotify.fetch_recently_played()

    repo.upsert_artists(artists)
    repo.upsert_tracks(tracks)
    new_plays = repo.add_plays(plays)

    return {
        "synced_artists": len(artists),
        "synced_tracks": len(tracks),
        "new_plays": new_plays,
        "genre_source": "lastfm" if settings.lastfm_api_key else "none (未設 LASTFM_API_KEY)",
    }


def get_top_artists(session: Session, limit: int = 10) -> list[TopArtistOut]:
    repo = MusicRepository(session)
    return [
        TopArtistOut(
            name=a.name,
            genres=json.loads(a.genres),
            rank=a.rank,
        )
        for a in repo.top_artists(limit)
    ]


def get_genre_distribution(session: Session) -> list[GenreCount]:
    repo = MusicRepository(session)
    # min_count=2:只保留至少 2 位歌手共有的曲風,砍掉長尾雜訊
    return compute_genre_distribution(repo.all_artist_genres(), min_count=2)


def get_heatmap(session: Session) -> list[list[int]]:
    repo = MusicRepository(session)
    return compute_heatmap(repo.all_play_times())
