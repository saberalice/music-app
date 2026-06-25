"""AI 歌單路由。

POST /playlists/parse     一句話 → 結構化條件(Day 4)
POST /playlists/generate  一句話 → 依曲風策略組出歌單(Day 5,讀)
POST /playlists/save      把歌單存回使用者的 Spotify(Day 5,寫)

路由薄:接請求 → 呼叫 service → 回傳。會打 Spotify 的端點要處理「沒登入」
與外部失敗,翻成對應 HTTP 狀態。
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_session
from app.models.schemas import (
    GeneratePlaylistOut,
    GenerateRequest,
    ParseRequest,
    PlaylistSpec,
    SavePlaylistOut,
    SaveRequest,
)
from app.repositories.recommendation_repository import RecommendationRepository
from app.services import context_service, playlist_service

router = APIRouter(tags=["playlists"])


@router.post("/playlists/parse")
def parse(req: ParseRequest) -> PlaylistSpec:
    """把一句話情境解析成歌單條件(LLM 失敗時回 fallback)。"""
    return context_service.parse_context(req.text)


@router.post("/playlists/generate")
def generate(
    req: GenerateRequest, session: Session = Depends(get_session)
) -> GeneratePlaylistOut:
    """一句話 → 解析 → 依曲風策略搜尋組歌單(尚未存回 Spotify)。

    會排除「先前推薦過」的曲目,所以同一句再產生一次會換一批
    (照相關度往下一順位)。想從頭來過用 /playlists/history/reset。
    """
    spec = context_service.parse_context(req.text)
    repo = RecommendationRepository(session)
    exclude = repo.get_recommended_uris()
    try:
        strategy_name, tracks = playlist_service.generate_playlist(
            spec, req.limit, exclude_uris=exclude
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"Spotify 搜尋失敗:{exc.response.text}"
        )
    # 記下這次推的,下次才會避開
    repo.add_recommended([t.uri for t in tracks])
    return GeneratePlaylistOut(strategy=strategy_name, spec=spec, tracks=tracks)


@router.post("/playlists/history/reset")
def reset_history(session: Session = Depends(get_session)) -> dict:
    """清空推薦歷史,下次產生會從最相關的重新開始。"""
    cleared = RecommendationRepository(session).clear()
    return {"cleared": cleared, "message": "推薦歷史已清空"}


@router.post("/playlists/save")
def save(req: SaveRequest) -> SavePlaylistOut:
    """把歌單存到使用者的 Spotify(會在你的帳號建立一個新歌單)。"""
    try:
        url, added = playlist_service.save_playlist(
            req.name, req.track_uris, description=req.description
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"存歌單失敗:{exc.response.text}"
        )
    return SavePlaylistOut(playlist_url=url, added=added)
