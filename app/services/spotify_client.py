"""呼叫 Spotify Web API 抓聽歌資料。

只用仍可用的端點:Top Artists / Top Tracks / Recently Played
(避開 2024/11 後被禁的 Recommendations、Audio Features)。

把「解析 Spotify 原始 JSON」拆成 module 層級的純函式 parse_*,
不依賴網路或 token,方便寫單元測試(見 tests/test_stats.py)。
"""

from datetime import datetime

import httpx

from app.models.schemas import ArtistDTO, PlayDTO, TrackDTO
from app.services.spotify_auth import API_BASE, SpotifyAuthService


# --- 純函式:原始 JSON → 乾淨 DTO(好測試)---
def parse_top_artists(payload: dict) -> list[ArtistDTO]:
    return [
        ArtistDTO(
            id=item["id"],
            name=item["name"],
            genres=item.get("genres", []),
            popularity=item.get("popularity", 0),
            rank=i + 1,  # items 已依常聽程度排序,index 0 = 第 1 名
        )
        for i, item in enumerate(payload.get("items", []))
    ]


def parse_top_tracks(payload: dict) -> list[TrackDTO]:
    tracks = []
    for i, item in enumerate(payload.get("items", [])):
        artists = item.get("artists", [])
        tracks.append(
            TrackDTO(
                id=item["id"],
                name=item["name"],
                artist_name=artists[0]["name"] if artists else "",
                album=item.get("album", {}).get("name", ""),
                popularity=item.get("popularity", 0),
                rank=i + 1,
            )
        )
    return tracks


def parse_recently_played(payload: dict) -> list[PlayDTO]:
    plays = []
    for item in payload.get("items", []):
        track = item["track"]
        artists = track.get("artists", [])
        # Spotify 給的是 UTC ISO 字串(結尾 Z),轉成 naive UTC datetime
        played_at = datetime.fromisoformat(
            item["played_at"].replace("Z", "+00:00")
        ).replace(tzinfo=None)
        plays.append(
            PlayDTO(
                track_id=track["id"],
                track_name=track["name"],
                artist_name=artists[0]["name"] if artists else "",
                played_at=played_at,
            )
        )
    return plays


class SpotifyClient:
    """負責實際發 HTTP 請求(會用到 token)。解析交給上面的純函式。"""

    def __init__(self, auth: SpotifyAuthService | None = None):
        self._auth = auth or SpotifyAuthService()

    def _get(self, path: str, params: dict | None = None) -> dict:
        token = self._auth.get_valid_access_token()
        if token is None:
            raise PermissionError("尚未登入 Spotify,請先走 /login 流程")
        resp = httpx.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def fetch_top_artists(
        self, limit: int = 20, time_range: str = "medium_term"
    ) -> list[ArtistDTO]:
        payload = self._get(
            "/me/top/artists", {"limit": limit, "time_range": time_range}
        )
        return parse_top_artists(payload)

    def fetch_top_tracks(
        self, limit: int = 20, time_range: str = "medium_term"
    ) -> list[TrackDTO]:
        payload = self._get(
            "/me/top/tracks", {"limit": limit, "time_range": time_range}
        )
        return parse_top_tracks(payload)

    def fetch_recently_played(self, limit: int = 50) -> list[PlayDTO]:
        payload = self._get("/me/player/recently-played", {"limit": limit})
        return parse_recently_played(payload)
