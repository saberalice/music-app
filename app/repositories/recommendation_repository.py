"""推薦歷史的存取層。

記錄「推薦過哪些曲目」,讓重新產生歌單時可以排除,做到不重複推薦。
唯一碰 recommended_track 表的地方。
"""

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.music import RecommendedTrack


class RecommendationRepository:
    def __init__(self, session: Session):
        self._s = session

    def get_recommended_uris(self) -> set[str]:
        """回傳所有推薦過的 URI(set,方便排除時做 in 判斷)。"""
        return set(self._s.scalars(select(RecommendedTrack.uri)))

    def add_recommended(self, uris: list[str]) -> None:
        """把這次推薦的曲目記進歷史(已存在的略過)。"""
        for uri in uris:
            if self._s.get(RecommendedTrack, uri) is None:
                self._s.add(RecommendedTrack(uri=uri))
        self._s.commit()

    def clear(self) -> int:
        """清空推薦歷史,回傳清掉的筆數。下次產生會從最相關的重新開始。"""
        count = len(self.get_recommended_uris())
        self._s.execute(delete(RecommendedTrack))
        self._s.commit()
        return count
