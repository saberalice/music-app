"""聽歌資料的 ORM model(對應 SQLite 資料表)。

三張表:歌手 artist、歌曲 track、播放紀錄 play_history。
schema 設計理由見 docs/design.md「Day 3」段落。
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Artist(Base):
    __tablename__ = "artist"

    # 直接用 Spotify 的 artist id 當主鍵,重複 sync 時可 upsert
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    # genres 是字串陣列,SQLite 沒有原生陣列,存成 JSON 字串
    genres: Mapped[str] = mapped_column(String, default="[]")
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    # 在 Top Artists 的名次(1 最常聽);非來自 top 榜的歌手為 None
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Track(Base):
    __tablename__ = "track"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    artist_name: Mapped[str] = mapped_column(String, default="")
    album: Mapped[str] = mapped_column(String, default="")
    popularity: Mapped[int] = mapped_column(Integer, default=0)
    rank: Mapped[int | None] = mapped_column(Integer, nullable=True)


class PlayHistory(Base):
    __tablename__ = "play_history"
    # 同一首歌在同一時間點只會有一筆 → 重複抓最近播放時自動去重
    __table_args__ = (UniqueConstraint("track_id", "played_at", name="uq_play"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    track_id: Mapped[str] = mapped_column(String)
    track_name: Mapped[str] = mapped_column(String)
    artist_name: Mapped[str] = mapped_column(String, default="")
    # Spotify 回傳 UTC 時間,這裡存 naive UTC(SQLite 不存時區)
    played_at: Mapped[datetime] = mapped_column(DateTime)
