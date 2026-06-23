"""向 Last.fm 查歌手曲風(補 Spotify 新 app 拿不到的 genres)。

用 artist.getTopTags 端點:Last.fm 上使用者替歌手標的標籤(tag),
最熱門的幾個通常就是曲風(rock / j-pop / classical…)。

解析拆成純函式 parse_top_tags 方便測試;網路請求集中在 LastfmClient。
任何一位歌手查詢失敗都不該讓整個 sync 崩掉,所以失敗回 [] 而非丟例外。

⚠️ tag 是使用者自由標的,會有雜訊(如 "seen live"),這裡單純取前 N 個熱門 tag,
夠用就好;要更乾淨可之後加白名單過濾。
"""

import httpx

LASTFM_API_BASE = "http://ws.audioscrobbler.com/2.0/"


def parse_top_tags(payload: dict, limit: int = 5) -> list[str]:
    """從 getTopTags 回應取出前 limit 個 tag 名稱(小寫,方便統計時合併)。"""
    tags = payload.get("toptags", {}).get("tag", [])
    # Last.fm 只有一個 tag 時會回 dict 而非 list,統一成 list
    if isinstance(tags, dict):
        tags = [tags]
    return [t["name"].lower() for t in tags[:limit] if t.get("name")]


# 非曲風的雜訊 tag:Last.fm 是使用者自由標的,常混入國籍、人聲描述、meta tag。
# 這裡只擋「明確不是曲風」的;同義詞正規化(jpop→j-pop)留待之後處理。
GENRE_BLOCKLIST = {
    # 國籍 / 地區
    "japanese", "japan", "chinese", "china", "korean", "korea",
    "british", "english", "american", "usa", "french", "france",
    "german", "germany", "spanish", "italian", "swedish", "taiwanese",
    # 人聲 / 角色描述
    "female vocalists", "female vocals", "male vocalists", "male vocals",
    "singer", "vocalist",
    # Last.fm 常見 meta tag
    "seen live", "favorites", "favourites", "favorite", "favourite",
    "composers", "composer",
}


def clean_genres(tags: list[str], artist_name: str = "", limit: int = 3) -> list[str]:
    """濾掉非曲風雜訊,去重後取前 limit 個。

    擋兩種:① 在 GENRE_BLOCKLIST 裡的;② 跟歌手名一樣的 tag
    (例如歌手「Wuthering Waves」被標 "wuthering waves")。
    先濾再取 limit,雜訊才不會佔掉名額。
    """
    blocked = GENRE_BLOCKLIST | {artist_name.lower()}
    cleaned: list[str] = []
    for tag in tags:
        if tag in blocked or tag in cleaned:
            continue
        cleaned.append(tag)
        if len(cleaned) == limit:
            break
    return cleaned


class LastfmClient:
    def __init__(self, api_key: str):
        self._api_key = api_key

    def fetch_genres(self, artist_name: str, limit: int = 3) -> list[str]:
        """查一位歌手的曲風(清理後取前 limit 個);沒設 key 或查詢失敗都回 []。"""
        if not self._api_key:
            return []
        try:
            resp = httpx.get(
                LASTFM_API_BASE,
                params={
                    "method": "artist.getTopTags",
                    "artist": artist_name,
                    "api_key": self._api_key,
                    "autocorrect": 1,  # 讓 Last.fm 自動修正歌手名
                    "format": "json",
                },
                timeout=10,
            )
            resp.raise_for_status()
            # 先抓一池(10 個)再清理,雜訊不會佔掉最終的 limit 名額
            tags = parse_top_tags(resp.json(), limit=10)
            return clean_genres(tags, artist_name, limit)
        except (httpx.HTTPError, KeyError, ValueError):
            return []
