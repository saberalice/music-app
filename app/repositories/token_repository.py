"""Token 存取層。

唯一負責「把 token 存到哪、怎麼讀回來」的地方。其他層(service / router)
只透過這裡存取,不直接碰檔案。

Day 2 先用一個本機 JSON 檔(單一使用者、自用 app 夠用);Day 3 之後若要
支援多使用者,改成寫進 SQLite 時,只要改這個檔,上層完全不用動——這就是
Repository pattern 的好處。

⚠️ 安全提醒:token 等同密碼,這裡是明碼存檔,只適合本機自用。正式多人服務
應加密或存進有權限控管的資料庫。檔案已被 .gitignore 排除。
"""

import json
from pathlib import Path

from app.models.spotify import TokenInfo

# 存在專案根目錄,檔名前面加點代表隱藏檔
_TOKEN_FILE = Path(".spotify_token.json")


class TokenRepository:
    def __init__(self, path: Path = _TOKEN_FILE):
        self._path = path

    def save(self, token: TokenInfo) -> None:
        """把 token 寫入檔案(覆蓋舊的)。"""
        self._path.write_text(token.model_dump_json(indent=2), encoding="utf-8")

    def load(self) -> TokenInfo | None:
        """讀回 token;沒存過(還沒登入)時回傳 None。"""
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return TokenInfo(**data)

    def clear(self) -> None:
        """刪除存檔(登出 / 重置用)。"""
        self._path.unlink(missing_ok=True)
