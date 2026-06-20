# 設計文件 — Music App

> 動手寫程式前,先在這裡用幾行字想清楚:要存什麼資料、有哪些 API、資料怎麼流。
> 這份文件會隨著開發逐步補完,不用一次寫滿。

## 一、這個 app 是什麼

一個自用的音樂 app,三大功能:
1. **聽歌統計** — 串 Spotify,抓自己的 Top Tracks / Artists / 最近播放,做統計圖表。
2. **AI 歌單產生器** — 打一句話(情境),用 LLM 解析成結構化條件,再到 Spotify 搜尋組歌單,可存回 Spotify。
3. **演唱會 / 音樂會通知** — 整合多個來源(Bandsintown / Songkick / 國家音樂廳爬蟲),定時通知。

## 二、技術棧

- 後端:Python 3.12 + FastAPI
- 資料庫:SQLite(透過 Repository 層存取)
- 前端:React (Vite) + Recharts
- 外部服務:Spotify Web API、Google Gemini API、Bandsintown / Songkick、OPENTIX 爬蟲

## 三、分層架構(關注點分離)

```
routers/      # 對外 API 端點,盡量薄,只做「接收請求 → 呼叫 service → 回傳」
services/     # 商業邏輯(OAuth 流程、組歌單、整合通知來源)
repositories/ # 資料存取,唯一直接碰資料庫的地方
models/       # 資料結構(Pydantic schema / ORM model)
core/         # 設定、共用工具(config、DB session、外部 client)
```

原則:**路由不直接碰資料庫**,一律經過 repository。

## 四、主要 API(規劃中,隨開發補完)

| 方法 | 路徑 | 功能 | 預計實作 |
|------|------|------|---------|
| GET  | `/health` | 健康檢查 | ✅ Day 1 |
| GET  | `/login` | 導向 Spotify 授權 | Day 2 |
| GET  | `/callback` | 接 Spotify OAuth callback,換 token | Day 2 |
| GET  | `/me` | 取得自己的 Spotify 個人資料 | Day 2 |
| GET  | `/stats/top-artists` | 最常聽歌手 Top 10 | Day 3 |
| GET  | `/stats/genres` | 曲風分佈 | Day 3 |
| POST | `/playlists/generate` | 用一句話產生歌單 | Day 5 |
| POST | `/playlists/save` | 把歌單存回 Spotify | Day 5 |
| GET  | `/concerts` | 近期演唱會 / 音樂會 | Day 9 |

## 五、三大功能的資料流(粗略)

### 聽歌統計
Spotify API → service 抓資料 → repository 存進 SQLite → 統計 service 算出結果 → 路由回傳 JSON → 前端畫圖。

### AI 歌單
使用者句子 → service 呼叫 Gemini → 解析成結構化 JSON → 依曲風選 SearchStrategy → 組 Spotify Search 查詢 → 組成歌單回傳。

### 演唱會通知
排程器定時 → 各 ConcertSource(Adapter)抓資料並轉成統一 Event → repository 去重 → 通知模組寄送。

## 六、設計模式對照(練習目標)

- **Repository pattern** — 聽歌統計的資料存取(Day 3)
- **Strategy pattern** — 依曲風分流的搜尋策略(Day 5)
- **Adapter pattern** — 多來源演唱會資料轉統一格式(Day 8)
- **分層架構** — 全專案
