"""Spotify 登入相關路由。

流程:
  GET /login    → 產生 state、組授權網址,把瀏覽器導去 Spotify
  GET /callback → Spotify 帶 code 導回這裡,驗 state、換 token、存起來
  GET /me       → 用存好的 token 呼叫 Spotify /me,驗證真的登入成功

路由本身很薄:接請求、呼叫 service、回傳結果。實際邏輯在 SpotifyAuthService。
"""

import secrets

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.services.spotify_auth import SpotifyAuthService

router = APIRouter(tags=["auth"])
service = SpotifyAuthService()

# 暫存已發出、還沒用掉的 state(防 CSRF)。自用單機夠用;
# 多 process 部署時應改放共用儲存(Redis / DB)。
_pending_states: set[str] = set()


@router.get("/login")
def login():
    """產生授權網址並把使用者導去 Spotify 同意畫面。"""
    state = secrets.token_urlsafe(16)
    _pending_states.add(state)
    url = service.build_authorize_url(state)
    return RedirectResponse(url)


@router.get("/callback")
def callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
):
    """接收 Spotify 導回的授權結果,換成 token 存起來。"""
    # 使用者按了「取消」,或 Spotify 回報錯誤
    if error:
        raise HTTPException(status_code=400, detail=f"Spotify 授權失敗:{error}")

    # 驗 state:必須是我們剛剛發出去、還沒用過的那一個
    if not state or state not in _pending_states:
        raise HTTPException(status_code=400, detail="state 不符,可能是 CSRF 或連結過期")
    _pending_states.discard(state)

    if not code:
        raise HTTPException(status_code=400, detail="缺少授權 code")

    try:
        service.exchange_code_for_token(code)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"向 Spotify 換 token 失敗:{exc.response.text}"
        )

    return {"message": "登入成功!可以打 GET /me 看你的 Spotify 個人資料了。"}


@router.get("/me")
def me():
    """用存好的 token 取得自己的 Spotify 個人資料。"""
    try:
        return service.get_current_user_profile()
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502, detail=f"呼叫 Spotify /me 失敗:{exc.response.text}"
        )
