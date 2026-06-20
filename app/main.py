"""FastAPI 應用程式進入點。

只負責「組裝」:建立 app、掛上各個 router。
實際的商業邏輯放在 services/,資料存取放在 repositories/,
路由本身盡量薄。
"""

from fastapi import FastAPI

from app.core.config import settings
from app.routers import health

app = FastAPI(title=settings.app_name)

# 掛上各功能的 router(目前只有 health,之後 spotify / playlists / concerts 陸續加入)
app.include_router(health.router)


@app.get("/")
def root():
    return {"message": f"{settings.app_name} is running. See /docs for the API."}
