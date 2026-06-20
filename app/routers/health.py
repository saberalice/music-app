"""健康檢查端點。

最小可動的第一個 API,用來確認服務有跑起來、
以及讓你打開 /docs 看 FastAPI 自動產生的互動式文件。
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """回傳服務狀態。部署後可用來做 uptime 監控。"""
    return {"status": "ok"}
