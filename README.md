# Music App

自用音樂 app:聽歌統計、AI 歌單產生器、演唱會/音樂會通知。
完整開發計畫見 [`musicapp.md`](musicapp.md),設計文件見 [`docs/design.md`](docs/design.md)。

## 技術棧

Python 3.12 + FastAPI(後端)、SQLite(資料庫)、React (Vite)(前端,Day 6 之後)。

## 本機跑起來

```bash
# 1. 建立並啟用 conda 環境
conda create -n musicapp python=3.12 -y
conda activate musicapp

# 2. 安裝依賴
pip install -r requirements.txt

# 3. 準備環境變數
cp .env.example .env   # 然後填入你的 key

# 4. 啟動後端
uvicorn app.main:app --reload
```

開瀏覽器看:

- http://localhost:8000/health — 健康檢查
- http://localhost:8000/docs — FastAPI 自動產生的互動式 API 文件

## 跑測試

```bash
pytest
```

## 架構

分層架構(關注點分離):

```
app/
  routers/      # API 端點
  services/     # 商業邏輯
  repositories/ # 資料存取
  models/       # 資料結構
  core/         # 設定、共用工具
```

設計模式:Repository(統計)、Strategy(歌單分流)、Adapter(演唱會來源)。
