"""聽歌統計路由。

POST /sync            從 Spotify 拉資料進 DB(要先登入過)
GET  /stats/top-artists  最常聽歌手 Top 10
GET  /stats/genres       曲風分佈
GET  /stats/heatmap      聽歌時段熱力圖(星期 × 小時)

路由只負責接請求、注入 DB session、呼叫 stats_service、把例外翻成 HTTP。
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.models.schemas import GenreCount, TopArtistOut
from app.services import stats_service

router = APIRouter(tags=["stats"])


@router.post("/sync")
def sync(session: Session = Depends(get_session)) -> dict:
    """從 Spotify 抓最新資料寫進 DB。"""
    try:
        return stats_service.sync_from_spotify(session)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"呼叫 Spotify 失敗:{exc.response.text}"
        )


@router.get("/stats/top-artists")
def top_artists(session: Session = Depends(get_session)) -> list[TopArtistOut]:
    return stats_service.get_top_artists(session, limit=10)


@router.get("/stats/genres")
def genres(session: Session = Depends(get_session)) -> list[GenreCount]:
    return stats_service.get_genre_distribution(session)


@router.get("/stats/heatmap")
def heatmap(session: Session = Depends(get_session)) -> dict:
    """回傳 7×24 矩陣;weekday[0]=星期一,hour[0]=00 點(UTC)。"""
    return {"grid": stats_service.get_heatmap(session)}
