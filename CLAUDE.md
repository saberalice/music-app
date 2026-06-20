# CLAUDE.md — AI 工具的專案 context

> 給 Claude Code / Cursor / Copilot 等 AI 工具參考,讓它產生的程式碼貼合本專案的架構與慣例。

## 專案簡介

自用音樂 app,三大功能:聽歌統計、AI 歌單產生器、演唱會/音樂會通知。
開發目標除了功能,更重視練好後端核心概念與設計模式。詳見 `docs/design.md` 與 `musicapp.md`。

## 技術棧

- 後端:Python 3.12、FastAPI、pydantic-settings
- 資料庫:SQLite(經 Repository 層存取)
- 測試:pytest、FastAPI TestClient
- 前端:React (Vite) + Recharts(Day 6 之後)
- 外部服務:Spotify Web API、Google Gemini、Bandsintown/Songkick、OPENTIX 爬蟲

## 目錄結構與分層

```
app/
  routers/      # API 路由,薄,只接請求→呼叫 service→回傳
  services/     # 商業邏輯
  repositories/ # 資料存取(唯一直接碰 DB 的地方)
  models/       # Pydantic / ORM 資料結構
  core/         # 設定 config、共用工具
docs/           # 設計文件
tests/          # pytest 測試
```

## 慣例與規則

- **路由不直接碰資料庫**,一律經過 repository。
- **secret 不寫死**:所有 key/secret 從 `app.core.config.settings` 取得,實際值放 `.env`(不進版控)。
- 命名:檔案與函式用 `snake_case`,類別用 `PascalCase`。
- 每個模組開頭寫簡短中文 docstring,說明用途。
- 設計模式對照:Repository(統計)、Strategy(歌單分流)、Adapter(演唱會來源)。

## Spotify 重要限制

2024/11 後新建的 app **不能用** Recommendations、Audio Features 端點(回 403)。
只用:Search、Top Tracks/Artists、Recently Played、已收藏、建立歌單。請勿產生用到被禁端點的程式碼。

## 開發紀律(請協助維持)

1. 動手前先在 `docs/` 補幾行設計。
2. AI 產生的程式碼要能逐行解釋才留下。
3. 小步 commit,訊息清楚。

## 常用指令

```bash
# 啟動後端(專案根目錄)
uvicorn app.main:app --reload

# 跑測試
pytest
```
