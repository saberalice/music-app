"""組歌單與存回 Spotify 的商業邏輯。

generate_playlist:選策略 → 各查詢去搜尋 → 去重 → 限量。
save_playlist:建立歌單 → 加歌 → 回傳歌單連結。

client 可注入,單元測試時用假 client 取代真網路。
"""

from app.models.schemas import PlaylistSpec, PlaylistTrack
from app.services.playlist_strategies import select_strategy
from app.services.spotify_client import SpotifyClient


# 這個 Spotify app 的 search limit 上限是 10,所以用 offset 一頁頁往下翻。
_PAGE_SIZE = 10
_MAX_OFFSET = 100  # 最多翻到約第 100 名,再往下相關度太低就不取了


def generate_playlist(
    spec: PlaylistSpec,
    limit: int = 20,
    client: SpotifyClient | None = None,
    exclude_uris: frozenset[str] | set[str] = frozenset(),
) -> tuple[str, list[PlaylistTrack]]:
    """依曲風策略組歌單,照相關度取曲,但跳過 exclude_uris(已推薦過的)。

    回傳 (策略名稱, 歌曲清單)。Spotify 搜尋已按相關度排序;這裡照順序往下走、
    遇到看過的就跳到下一順位(必要時用 offset 翻頁取更深的候選),所以結果仍
    貼題,只是換一批。
    """
    client = client or SpotifyClient()
    strategy = select_strategy(spec)
    queries = strategy.build_queries(spec)

    tracks: list[PlaylistTrack] = []
    seen: set[str] = set(exclude_uris)  # 推薦過的當作「已看過」,直接略過
    for query in queries:
        offset = 0
        while offset <= _MAX_OFFSET:
            page = client.search_tracks(
                query, market=strategy.market, limit=_PAGE_SIZE, offset=offset
            )
            if not page:
                break  # 這個查詢沒有更多結果了
            for track in page:
                if track.uri in seen:
                    continue
                seen.add(track.uri)
                tracks.append(track)
                if len(tracks) >= limit:
                    return strategy.name, tracks
            offset += _PAGE_SIZE
    return strategy.name, tracks


def save_playlist(
    name: str,
    track_uris: list[str],
    description: str = "",
    client: SpotifyClient | None = None,
) -> tuple[str, int]:
    """把歌單存到使用者的 Spotify。回傳 (歌單連結, 加入的歌曲數)。"""
    client = client or SpotifyClient()
    user_id = client.get_user_id()
    playlist = client.create_playlist(user_id, name, description=description)
    client.add_tracks(playlist["id"], track_uris)
    return playlist["external_urls"]["spotify"], len(track_uris)
