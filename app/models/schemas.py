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
