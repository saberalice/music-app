"""Pydantic 資料結構(DTO 與 API 回應)。

跟 ORM model(music.py)分開:
- DTO(ArtistDTO 等):從 Spotify 解析出來、要傳給 repository 的「乾淨資料」,
  讓 service / repository 不用直接面對 Spotify 原始 JSON 的雜亂結構。
- 回應 model(GenreCount 等):API 回傳的形狀,順便讓 /docs 自動產生 schema。
"""

from datetime import datetime

from pydantic import BaseModel


# --- 從 Spotify 解析出的 DTO ---
class ArtistDTO(BaseModel):
    id: str
    name: str
    genres: list[str] = []
    popularity: int = 0
    rank: int | None = None


class TrackDTO(BaseModel):
    id: str
    name: str
    artist_name: str = ""
    album: str = ""
    popularity: int = 0
    rank: int | None = None


class PlayDTO(BaseModel):
    track_id: str
    track_name: str
    artist_name: str = ""
    played_at: datetime


# --- API 回應 ---
class GenreCount(BaseModel):
    genre: str
    count: int


class TopArtistOut(BaseModel):
    name: str
    genres: list[str]
    rank: int | None = None
    # 註:Spotify 新 app 拿不到 popularity,故不提供


# --- Day 4:AI 歌單 ---
class ParseRequest(BaseModel):
    """使用者輸入的一句話情境。"""

    text: str


class PlaylistSpec(BaseModel):
    """Gemini 把一句話解析成的結構化歌單條件(Day 5 用來組搜尋)。"""

    genre: str | None = None
    mood: str | None = None
    era: str | None = None
    seed_artists: list[str] = []
    keywords: list[str] = []


# --- Day 5:組歌單 ---
class PlaylistTrack(BaseModel):
    """一首搜尋到的歌(給前端顯示 + 存回 Spotify 用)。"""

    id: str
    name: str
    artist: str = ""
    album: str = ""
    uri: str  # spotify:track:... 存歌單時用
    spotify_url: str = ""
    image: str | None = None


class GenerateRequest(BaseModel):
    text: str
    limit: int = 20


class GeneratePlaylistOut(BaseModel):
    strategy: str  # 實際用了哪個策略(jpop / classical / default)
    spec: PlaylistSpec
    tracks: list[PlaylistTrack]


class SaveRequest(BaseModel):
    name: str
    track_uris: list[str]
    description: str = "由 music app 產生"


class SavePlaylistOut(BaseModel):
    playlist_url: str
    added: int
