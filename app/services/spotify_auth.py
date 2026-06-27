"""Spotify OAuth 商業邏輯。

實作 Authorization Code 流程:
  1. build_authorize_url() 產生「請使用者去 Spotify 授權」的網址
  2. 使用者同意後,Spotify 帶著 code 導回我們的 /callback
  3. exchange_code_for_token() 拿 code 去換 access/refresh token
  4. get_valid_access_token() 之後每次要打 API 前呼叫,過期會自動用
     refresh token 換新

token 的存讀都委託給 TokenRepository,本檔不直接碰檔案/DB。
"""

import base64
import time

import httpx

from app.core.config import settings
from app.models.spotify import TokenInfo
from app.repositories.token_repository import TokenRepository

# Spotify 端點
AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"

# 要跟使用者要的授權範圍。只列本專案會用到、且仍可用的端點所需 scope。
# (避免被禁的 Recommendations / Audio Features)
SCOPES = " ".join(
    [
        "user-read-private",          # /me 個人資料
        "user-read-email",
        "user-top-read",              # Day 3:Top Tracks / Artists
        "user-read-recently-played",  # Day 3:最近播放
        "user-library-read",          # 已收藏
        "playlist-modify-public",     # Day 5:建立 / 修改歌單
        "playlist-modify-private",
    ]
)


def _basic_auth_header() -> dict[str, str]:
    """Spotify 換 token 時要用 HTTP Basic 帶上 client_id:client_secret。"""
    raw = f"{settings.spotify_client_id}:{settings.spotify_client_secret}"
    encoded = base64.b64encode(raw.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


class SpotifyAuthService:
    def __init__(self, repo: TokenRepository | None = None):
        self._repo = repo or TokenRepository()

    # --- 第 1 步:產生授權網址 ---
    def build_authorize_url(self, state: str) -> str:
        """組出導向 Spotify 的授權網址。

        state 是隨機字串,用來防 CSRF:callback 回來時要比對一致才算數。
        """
        params = {
            "client_id": settings.spotify_client_id,
            "response_type": "code",
            "redirect_uri": settings.spotify_redirect_uri,
            "scope": SCOPES,
            "state": state,
        }
        query = httpx.QueryParams(params)
        return f"{AUTHORIZE_URL}?{query}"

    # --- 第 3 步:用 code 換 token ---
    def exchange_code_for_token(self, code: str) -> TokenInfo:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.spotify_redirect_uri,
        }
        token = self._request_token(data)
        self._repo.save(token)
        return token

    def logout(self) -> None:
        """清除存的 token(登出)。下次要用得重新走 /login。"""
        self._repo.clear()

    # --- 第 4 步:確保拿到一個沒過期的 access token ---
    def get_valid_access_token(self) -> str | None:
        """回傳可用的 access token;沒登入過回 None,過期則自動刷新。"""
        token = self._repo.load()
        if token is None:
            return None
        if token.is_expired():
            token = self._refresh(token)
        return token.access_token

    def _refresh(self, token: TokenInfo) -> TokenInfo:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": token.refresh_token,
        }
        new_token = self._request_token(data, fallback_refresh_token=token.refresh_token)
        self._repo.save(new_token)
        return new_token

    def _request_token(
        self, data: dict, fallback_refresh_token: str | None = None
    ) -> TokenInfo:
        """實際打 Spotify token 端點,把回應轉成 TokenInfo。

        刷新時 Spotify 不一定會回傳新的 refresh_token,沒回就沿用舊的。
        """
        resp = httpx.post(TOKEN_URL, data=data, headers=_basic_auth_header(), timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        return TokenInfo(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token") or fallback_refresh_token or "",
            token_type=payload.get("token_type", "Bearer"),
            scope=payload.get("scope", ""),
            expires_at=time.time() + payload["expires_in"],
        )

    # --- 用 token 呼叫 /me 驗證 ---
    def get_current_user_profile(self) -> dict:
        """呼叫 Spotify /me,回傳自己的個人資料。沒登入會丟 PermissionError。"""
        access_token = self.get_valid_access_token()
        if access_token is None:
            raise PermissionError("尚未登入 Spotify,請先走 /login 流程")
        resp = httpx.get(
            f"{API_BASE}/me",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
