"""呼叫 Spotify Web API 抓聽歌資料。

只用仍可用的端點:Top Artists / Top Tracks / Recently Played
(避開 2024/11 後被禁的 Recommendations、Audio Features)。

把「解析 Spotify 原始 JSON」拆成 module 層級的純函式 parse_*,
不依賴網路或 token,方便寫單元測試(見 tests/test_stats.py)。
"""

from datetime import datetime

import httpx

from app.models.schemas import ArtistDTO, PlaylistTrack, PlayDTO, TrackDTO
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


def parse_search_tracks(payload: dict) -> list[PlaylistTrack]:
    """把 /search 的回應轉成 PlaylistTrack。"""
    tracks = []
    for item in payload.get("tracks", {}).get("items", []):
        artists = item.get("artists", [])
        album = item.get("album", {})
        images = album.get("images", [])
        tracks.append(
            PlaylistTrack(
                id=item["id"],
                name=item["name"],
                artist=artists[0]["name"] if artists else "",
                album=album.get("name", ""),
                uri=item["uri"],
                spotify_url=item.get("external_urls", {}).get("spotify", ""),
                image=images[0]["url"] if images else None,
            )
        )
    return tracks


class SpotifyClient:
    """負責實際發 HTTP 請求(會用到 token)。解析交給上面的純函式。"""

    def __init__(self, auth: SpotifyAuthService | None = None):
        self._auth = auth or SpotifyAuthService()

    def _headers(self) -> dict[str, str]:
        token = self._auth.get_valid_access_token()
        if token is None:
            raise PermissionError("尚未登入 Spotify,請先走 /login 流程")
        return {"Authorization": f"Bearer {token}"}

    def _get(self, path: str, params: dict | None = None) -> dict:
        resp = httpx.get(
            f"{API_BASE}{path}", headers=self._headers(), params=params, timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, json_body: dict) -> dict:
        resp = httpx.post(
            f"{API_BASE}{path}", headers=self._headers(), json=json_body, timeout=10
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

    # --- Day 5:搜尋與組歌單 ---
    def search_tracks(
        self,
        query: str,
        market: str | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[PlaylistTrack]:
        # 注意:這個 app 的 search limit 上限是 10(超過回 400),用 offset 翻頁取更多
        params: dict = {"q": query, "type": "track", "limit": min(limit, 10), "offset": offset}
        if market:
            params["market"] = market
        return parse_search_tracks(self._get("/search", params))

    def get_user_id(self) -> str:
        return self._get("/me")["id"]

    def create_playlist(
        self, user_id: str, name: str, description: str = "", public: bool = False
    ) -> dict:
        """建立空歌單,回傳 Spotify 的 playlist 物件(含 id 與外部連結)。"""
        return self._post(
            f"/users/{user_id}/playlists",
            {"name": name, "description": description, "public": public},
        )

    def add_tracks(self, playlist_id: str, uris: list[str]) -> None:
        # Spotify 一次最多加 100 首,超過要分批
        for i in range(0, len(uris), 100):
            self._post(f"/playlists/{playlist_id}/tracks", {"uris": uris[i : i + 100]})
