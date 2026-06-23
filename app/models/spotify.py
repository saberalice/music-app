"""Spotify 相關的資料結構。

目前只有 token,之後 Day 3 抓歌曲/歌手時會再加 Track、Artist 等。
"""

import time

from pydantic import BaseModel


class TokenInfo(BaseModel):
    """一組 Spotify OAuth token。

    Spotify 換 token 時回傳的是 `expires_in`(秒數),我們在拿到的當下
    換算成絕對到期時間 `expires_at`(unix timestamp),之後判斷有沒有過期
    才不用每次重算。
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    scope: str = ""
    expires_at: float  # unix timestamp,access_token 何時失效

    def is_expired(self, leeway_seconds: int = 60) -> bool:
        """是否已過期(或即將過期)。

        留 60 秒緩衝,避免「剛好沒過期但送出時就過期」的邊界情況。
        """
        return time.time() >= (self.expires_at - leeway_seconds)
