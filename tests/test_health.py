"""health 端點的測試。

用 FastAPI 的 TestClient,不需要真的開 server 就能打 API。
跑法:在專案根目錄執行 `pytest`
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
