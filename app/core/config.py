"""集中管理設定與 secret。

重點:API key / client secret 絕對不寫死在程式碼裡,
而是從環境變數或 .env 讀進來。pydantic-settings 會自動
讀取 .env,並做型別驗證。

實際的 .env 不會進版控(看 .gitignore),團隊用 .env.example
當範本。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 一般設定
    app_name: str = "Music App"

    # Spotify(Day 2 開始用)
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    # 注意:Spotify 2025 起不接受 http://localhost,本機要用 loopback IP 127.0.0.1
    spotify_redirect_uri: str = "http://127.0.0.1:8000/callback"

    # Gemini(Day 4 開始用)
    gemini_api_key: str = ""

    # 資料庫(Day 3 開始用)
    database_url: str = "sqlite:///./musicapp.db"


# 全專案共用同一個 settings 實例
settings = Settings()
