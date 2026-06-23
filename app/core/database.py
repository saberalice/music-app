"""資料庫連線與 session 管理(SQLAlchemy)。

集中放 engine、session 工廠、Base。其他層不自己建連線,
要用 DB 時透過 get_session() 取得 session。

- engine:對應一個資料庫(這裡是 SQLite 檔)
- SessionLocal:產生 session 的工廠,一次請求用一個 session
- Base:所有 ORM model 繼承它,SQLAlchemy 才知道有哪些表
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """所有 ORM model 的共同基底。"""


# check_same_thread=False:FastAPI 可能在不同執行緒用同一連線,SQLite 預設會擋
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """建立所有資料表(若不存在)。app 啟動時呼叫一次。"""
    # import 進來才會把 model 註冊到 Base.metadata
    from app.models import music  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_session():
    """FastAPI 依賴注入用:每個請求拿一個 session,用完關掉。"""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
