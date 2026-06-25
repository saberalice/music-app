"""AI 歌單路由。

Day 4 先做「解析」:把一句話轉成結構化 PlaylistSpec,方便單獨驗證 LLM 解析。
Day 5 會再加 POST /playlists/generate(接 Strategy 組真正的歌單)。

路由很薄:接請求 → 呼叫 context_service → 回傳。fallback 在 service 裡處理,
所以這裡不需要 try/except(永遠拿得到一個 PlaylistSpec)。
"""

from fastapi import APIRouter

from app.models.schemas import ParseRequest, PlaylistSpec
from app.services import context_service

router = APIRouter(tags=["playlists"])


@router.post("/playlists/parse")
def parse(req: ParseRequest) -> PlaylistSpec:
    """把一句話情境解析成歌單條件(LLM 失敗時回 fallback)。"""
    return context_service.parse_context(req.text)
