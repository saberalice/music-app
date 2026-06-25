"""Day 5 Strategy 與組歌單測試。

策略是純邏輯直接測;組歌單用假 client 取代 Spotify,驗去重與限量。
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import music  # noqa: F401  讓 Base 認得這些表
from app.models.schemas import PlaylistSpec, PlaylistTrack
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.playlist_service import generate_playlist
from app.services.playlist_strategies import (
    ClassicalStrategy,
    DefaultStrategy,
    JpopStrategy,
    select_strategy,
)
from app.services.spotify_client import parse_search_tracks


# --- 選擇器 ---
def test_select_strategy_by_genre():
    assert isinstance(select_strategy(PlaylistSpec(genre="classical")), ClassicalStrategy)
    assert isinstance(select_strategy(PlaylistSpec(genre="j-pop")), JpopStrategy)
    assert isinstance(select_strategy(PlaylistSpec(genre="j-rock")), JpopStrategy)
    assert isinstance(select_strategy(PlaylistSpec(genre="jazz")), DefaultStrategy)
    assert isinstance(select_strategy(PlaylistSpec(genre=None)), DefaultStrategy)


# --- 各策略 build_queries ---
def test_jpop_strategy_uses_jp_market_and_artist_filter():
    s = JpopStrategy()
    assert s.market == "JP"
    queries = s.build_queries(PlaylistSpec(genre="j-pop", seed_artists=["YOASOBI"], keywords=["energetic"]))
    assert "artist:YOASOBI" in queries
    assert any("energetic" in q and "j-pop" in q for q in queries)


def test_classical_strategy_combines_composer_and_form():
    s = ClassicalStrategy()
    queries = s.build_queries(PlaylistSpec(genre="classical", seed_artists=["Chopin"], keywords=["nocturne", "sonata"]))
    assert "Chopin nocturne" in queries
    assert "Chopin sonata" in queries


def test_default_strategy_combines_genre_mood_keywords():
    s = DefaultStrategy()
    queries = s.build_queries(PlaylistSpec(genre="jazz", mood="calm", keywords=["rainy"]))
    assert "jazz calm rainy" in queries


def test_strategy_falls_back_when_spec_empty():
    # 沒有任何條件時也要產生至少一個查詢,不會回空
    assert DefaultStrategy().build_queries(PlaylistSpec()) == ["music"]


# --- 搜尋解析 ---
def test_parse_search_tracks_extracts_fields():
    payload = {
        "tracks": {
            "items": [
                {
                    "id": "1",
                    "name": "Song A",
                    "uri": "spotify:track:1",
                    "artists": [{"name": "Artist X"}],
                    "album": {"name": "Album Y", "images": [{"url": "http://img"}]},
                    "external_urls": {"spotify": "http://open/1"},
                }
            ]
        }
    }
    tracks = parse_search_tracks(payload)
    assert tracks[0].uri == "spotify:track:1"
    assert tracks[0].artist == "Artist X"
    assert tracks[0].image == "http://img"


# --- 組歌單(假 client)---
def _track(n: str) -> PlaylistTrack:
    return PlaylistTrack(id=n, name=f"Song {n}", uri=f"spotify:track:{n}")


class _FakeClient:
    def __init__(self, mapping):
        self._mapping = mapping
        self.calls = []

    def search_tracks(self, query, market=None, limit=10, offset=0):
        self.calls.append((query, market, limit, offset))
        if offset > 0:
            return []  # 模擬每個查詢只有一頁,翻頁就見底
        return self._mapping.get(query, [])


def test_generate_playlist_dedupes_and_limits():
    # 兩個查詢,結果有重疊(t2);limit=3 應去重後截斷
    fake = _FakeClient(
        {
            "a": [_track("1"), _track("2")],
            "b": [_track("2"), _track("3"), _track("4")],
        }
    )
    spec = PlaylistSpec(keywords=["a", "b"])  # DefaultStrategy → 查詢 ["a", "b"]
    strategy_name, tracks = generate_playlist(spec, limit=3, client=fake)

    assert strategy_name == "default"
    uris = [t.uri for t in tracks]
    assert uris == ["spotify:track:1", "spotify:track:2", "spotify:track:3"]  # 去重 + 限 3


def test_generate_playlist_excludes_recommended_history():
    # 排除 t1、t2(已推薦過)→ 照相關度往下取 t3、t4
    fake = _FakeClient({"a": [_track("1"), _track("2"), _track("3"), _track("4")]})
    spec = PlaylistSpec(keywords=["a"])
    _, tracks = generate_playlist(
        spec, limit=2, client=fake, exclude_uris={"spotify:track:1", "spotify:track:2"}
    )
    assert [t.uri for t in tracks] == ["spotify:track:3", "spotify:track:4"]


def test_recommendation_repository_records_and_clears():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    repo = RecommendationRepository(sessionmaker(bind=engine)())

    repo.add_recommended(["spotify:track:1", "spotify:track:2"])
    repo.add_recommended(["spotify:track:2", "spotify:track:3"])  # t2 重複,應略過
    assert repo.get_recommended_uris() == {
        "spotify:track:1",
        "spotify:track:2",
        "spotify:track:3",
    }
    assert repo.clear() == 3
    assert repo.get_recommended_uris() == set()
