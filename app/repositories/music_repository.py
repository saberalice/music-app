"""聽歌資料的存取層。

唯一直接碰 SQLite 的地方。上層(service)給它乾淨的 DTO,
它負責寫進表、或從表撈出來。JSON 編解碼(genres)也封在這裡,
讓 service 拿到的永遠是 Python list,不用管儲存細節。
"""

import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.music import Artist, PlayHistory, Track
from app.models.schemas import ArtistDTO, PlayDTO, TrackDTO


class MusicRepository:
    def __init__(self, session: Session):
        self._s = session

    # --- 寫入 ---
    def upsert_artists(self, artists: list[ArtistDTO]) -> None:
        """有就更新、沒有就新增(以 Spotify id 為準)。"""
        for a in artists:
            obj = self._s.get(Artist, a.id)
            if obj is None:
                obj = Artist(id=a.id)
                self._s.add(obj)
            obj.name = a.name
            obj.genres = json.dumps(a.genres)  # list → JSON 字串
            obj.popularity = a.popularity
            obj.rank = a.rank
        self._s.commit()

    def upsert_tracks(self, tracks: list[TrackDTO]) -> None:
        for t in tracks:
            obj = self._s.get(Track, t.id)
            if obj is None:
                obj = Track(id=t.id)
                self._s.add(obj)
            obj.name = t.name
            obj.artist_name = t.artist_name
            obj.album = t.album
            obj.popularity = t.popularity
            obj.rank = t.rank
        self._s.commit()

    def add_plays(self, plays: list[PlayDTO]) -> int:
        """新增播放紀錄,已存在的(track_id + played_at 相同)跳過。回傳新增筆數。"""
        added = 0
        for p in plays:
            exists = self._s.scalar(
                select(PlayHistory).where(
                    PlayHistory.track_id == p.track_id,
                    PlayHistory.played_at == p.played_at,
                )
            )
            if exists:
                continue
            self._s.add(
                PlayHistory(
                    track_id=p.track_id,
                    track_name=p.track_name,
                    artist_name=p.artist_name,
                    played_at=p.played_at,
                )
            )
            added += 1
        self._s.commit()
        return added

    # --- 讀取 ---
    def top_artists(self, limit: int = 10) -> list[Artist]:
        """依名次排序的常聽歌手(只取有 rank 的)。"""
        return list(
            self._s.scalars(
                select(Artist)
                .where(Artist.rank.is_not(None))
                .order_by(Artist.rank)
                .limit(limit)
            )
        )

    def all_artist_genres(self) -> list[list[str]]:
        """撈出每位歌手的 genres(已解回 Python list)。"""
        rows = self._s.scalars(select(Artist.genres)).all()
        return [json.loads(g) for g in rows]

    def all_play_times(self) -> list[datetime]:
        """撈出所有播放時間,給熱力圖彙總用。"""
        return list(self._s.scalars(select(PlayHistory.played_at)))
