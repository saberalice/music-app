"""Day 3 統計相關測試。

分兩類:
1. 純函式:解析 Spotify JSON、彙總統計 —— 不碰網路/DB,最好測。
2. Repository:用 in-memory SQLite 驗證 ORM 寫入、查詢、去重真的會動。
"""

from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import music  # noqa: F401  讓 Base 認得這些表
from app.models.schemas import ArtistDTO, PlayDTO
from app.repositories.music_repository import MusicRepository
from app.services.lastfm_client import clean_genres, parse_top_tags
from app.services.spotify_client import parse_recently_played
from app.services.stats_service import (
    compute_genre_distribution,
    compute_heatmap,
)


# --- 純函式 ---
def test_parse_recently_played_extracts_fields():
    payload = {
        "items": [
            {
                "played_at": "2026-06-20T15:30:00.000Z",
                "track": {
                    "id": "t1",
                    "name": "Song A",
                    "artists": [{"name": "Artist X"}, {"name": "Artist Y"}],
                },
            }
        ]
    }
    plays = parse_recently_played(payload)
    assert len(plays) == 1
    assert plays[0].track_id == "t1"
    assert plays[0].track_name == "Song A"
    assert plays[0].artist_name == "Artist X"  # 取第一位歌手
    # Z(UTC)被轉成 naive datetime
    assert plays[0].played_at == datetime(2026, 6, 20, 15, 30, 0)


def test_parse_top_tags_takes_top_n_lowercased():
    payload = {
        "toptags": {
            "tag": [
                {"name": "J-Pop", "count": 100},
                {"name": "Rock", "count": 80},
                {"name": "anime", "count": 60},
            ]
        }
    }
    assert parse_top_tags(payload, limit=2) == ["j-pop", "rock"]


def test_parse_top_tags_handles_single_tag_as_dict():
    # Last.fm 只有一個 tag 時回 dict 而非 list
    payload = {"toptags": {"tag": {"name": "Classical", "count": 100}}}
    assert parse_top_tags(payload) == ["classical"]


def test_parse_top_tags_empty_when_no_tags():
    # 查不到歌手 / 錯誤回應
    assert parse_top_tags({"error": 6, "message": "not found"}) == []


def test_clean_genres_filters_noise_and_truncates():
    # blocklist(japanese)、歌手同名(wuthering waves)、重複都要濾掉,最後取前 3
    tags = ["japanese", "wuthering waves", "soundtrack", "video game music",
            "chinese", "instrumental", "soundtrack"]
    result = clean_genres(tags, artist_name="Wuthering Waves", limit=3)
    assert "japanese" not in result
    assert "wuthering waves" not in result
    assert result == ["soundtrack", "video game music", "instrumental"]


def test_compute_genre_distribution_counts_and_sorts():
    artists_genres = [["jazz", "pop"], ["jazz"], ["rock", "jazz"]]
    result = compute_genre_distribution(artists_genres)
    # jazz 出現 3 次,排第一
    assert result[0].genre == "jazz"
    assert result[0].count == 3
    # 總共三種曲風
    assert {gc.genre for gc in result} == {"jazz", "pop", "rock"}


def test_compute_genre_distribution_min_count_drops_long_tail():
    artists_genres = [["jazz", "pop"], ["jazz"], ["rock"]]
    # min_count=2:只有 jazz(2 次)留下,pop / rock(各 1 次)被砍
    result = compute_genre_distribution(artists_genres, min_count=2)
    assert [gc.genre for gc in result] == ["jazz"]


def test_compute_heatmap_places_play_in_right_cell():
    d = datetime(2026, 6, 22, 15, 0)  # 某個星期一下午 3 點
    grid = compute_heatmap([d, d])
    assert grid[d.weekday()][15] == 2
    # 其他格子都是 0,總和等於播放數
    assert sum(sum(row) for row in grid) == 2


# --- Repository(in-memory DB)---
def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_repository_upsert_and_top_artists():
    session = _make_session()
    repo = MusicRepository(session)
    repo.upsert_artists(
        [
            ArtistDTO(id="a1", name="Alpha", genres=["jazz"], popularity=80, rank=1),
            ArtistDTO(id="a2", name="Beta", genres=["pop", "jazz"], popularity=70, rank=2),
        ]
    )
    top = repo.top_artists(limit=10)
    assert [a.name for a in top] == ["Alpha", "Beta"]  # 依 rank 排序
    # genres 解回 list,可給彙總用
    assert repo.all_artist_genres() == [["jazz"], ["pop", "jazz"]]


def test_repository_add_plays_deduplicates():
    session = _make_session()
    repo = MusicRepository(session)
    play = PlayDTO(
        track_id="t1",
        track_name="Song A",
        artist_name="Artist X",
        played_at=datetime(2026, 6, 20, 15, 30, 0),
    )
    # 第一次新增 1 筆
    assert repo.add_plays([play]) == 1
    # 同一筆再 sync 一次 → 去重,不重複新增
    assert repo.add_plays([play]) == 0
    assert len(repo.all_play_times()) == 1
