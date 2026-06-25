"""FastAPI 應用程式進入點。

只負責「組裝」:建立 app、掛上各個 router、啟動時初始化資料庫。
實際的商業邏輯放在 services/,資料存取放在 repositories/,
路由本身盡量薄。
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.core.database import init_db
from app.routers import auth, health, playlists, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    # app 啟動時建立資料表(已存在則略過),關閉時不用特別處理
    init_db()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# 掛上各功能的 router(之後 playlists / concerts 陸續加入)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(playlists.router)


@app.get("/")
def root():
    return {"message": f"{settings.app_name} is running. See /docs for the API."}
