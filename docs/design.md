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

## 五之一、Day 3 聽歌統計 — 資料表與端點設計

### 要存什麼(SQLite,透過 SQLAlchemy ORM)

- **artist**(歌手):`id`(Spotify id, PK)、`name`、`genres`(JSON 字串)、`popularity`、`rank`(在 Top Artists 的名次,越小越常聽)
- **track**(歌曲):`id`(PK)、`name`、`artist_name`、`album`、`popularity`、`rank`
- **play_history**(播放紀錄):`id`(自增 PK)、`track_id`、`track_name`、`artist_name`、`played_at`
  - `(track_id, played_at)` 設唯一鍵 → 重複抓最近播放時自動去重

### 資料流

1. `POST /sync` → service 用 Day 2 的 token 打 Spotify(Top Artists / Top Tracks / Recently Played)
   → 純函式 `parse_*` 把回應轉成乾淨 DTO → repository 寫進 SQLite(upsert / 去重)。
2. `GET /stats/*` → repository 從 SQLite 撈出 → service 用純函式做彙總 → router 回 JSON。

### 端點

| 方法 | 路徑 | 說明 |
|------|------|------|
| POST | `/sync` | 從 Spotify 拉資料進 DB(要先登入過) |
| GET  | `/stats/top-artists` | 最常聽歌手 Top 10(依 rank) |
| GET  | `/stats/genres` | 曲風分佈(彙總所有歌手的 genres) |
| GET  | `/stats/heatmap` | (進階)聽歌時段熱力圖,星期 × 小時 |

### 為什麼這樣分

- 抓資料(client)、存取(repository)、彙總(service 純函式)分開 → 彙總邏輯不碰 DB/網路,**單元測試好寫**。
- 只用仍可用的 Spotify 端點(Top、Recently Played),避開被禁的 Recommendations / Audio Features。

### 踩到的真實限制:曲風改用 Last.fm

實測發現 Spotify 對 2024/11 後新建的 app **拔掉了 artist 的 `genres` 與 `popularity`**
(top/single 端點都不回,批次 `/artists?ids=` 回 403)。因此:
- `popularity` 拿不到 → 不再顯示。
- 曲風改由 **Last.fm `artist.getTopTags`** 補:sync 時逐位歌手查標籤當曲風。
  這一步讓同一個 `ArtistDTO` 的資料來自兩個來源(Spotify + Last.fm),正好是 Day 8
  多來源整合 / Adapter 的雛形。沒設 `LASTFM_API_KEY` 時 genres 維持空,功能不崩。

## 五之二、Day 4 AI 解析情境 → 結構化 JSON

### 目標
使用者一句話(例:「下雨的午後想專心工作的爵士」)→ 用 Gemini 解析成固定格式 JSON:

```json
{ "genre": "jazz", "mood": "calm", "era": null,
  "seed_artists": [], "keywords": ["rainy", "focus", "instrumental"] }
```

### 怎麼接
- **httpx 直接打 Gemini REST**:`POST .../models/{model}:generateContent?key=...`
- 用 `responseMimeType: application/json` 要求只回 JSON;prompt 也明講「只回 JSON」。
- 模型:`gemini-2.5-flash`(可由 `GEMINI_MODEL` 調)。

### 分層
- `services/gemini_client.py`:組 prompt、打 API、抽出回應文字(純函式 `build_prompt`、
  `extract_text`、`parse_spec` 方便測試)。
- `services/context_service.py`:`parse_context(sentence)` 編排 + **fallback**。
- `routers/playlists.py`:`POST /playlists/parse`(Day 4 先做解析,Day 5 再接 Strategy 組歌單)。
- `models/schemas.py`:`PlaylistSpec`(解析結果)、`ParseRequest`。

### 重點:錯誤處理與 fallback(Day 4 的核心學習)
LLM 可能回傳壞 JSON、夾 markdown、API 逾時或額度用完。對策:
- `parse_spec` 容錯解析(去除 ```json 圍欄、缺欄位用預設)。
- `parse_context` 用 try/except 包住;**失敗時 fallback**:至少用整句當 keyword,
  讓下游(Day 5 搜尋)還能運作,不會整個崩。

## 五之三、Day 5 依曲風分流組歌單(Strategy pattern)

### 目標
把 Day 4 的 `PlaylistSpec` 依曲風用**不同策略**轉成 Spotify Search 查詢,
組成歌單,並可存回 Spotify。

### Strategy pattern
共同介面 `SearchStrategy.build_queries(spec) -> list[str]`,三個實作:
- `JpopStrategy`:帶日本市場(`market=JP`),用 `artist:` + 關鍵字 + j-pop。
- `ClassicalStrategy`:用「作曲家 + 曲式」搜(如 `Chopin nocturne`),
  seed_artists 常是作曲家。
- `DefaultStrategy`:genre + mood + 關鍵字組一般查詢。
`select_strategy(spec)` 依 `spec.genre` 挑策略 —— 新增曲風只要加一個 class,
不用改既有程式(這就是 Strategy 的好處)。

### 分層
- `services/playlist_strategies.py`:策略介面與實作(純邏輯,好測試)。
- `services/playlist_service.py`:`generate_playlist`(選策略→搜尋→去重→限量)、
  `save_playlist`(建歌單+加歌)。
- `services/spotify_client.py`:加 `search_tracks`、`create_playlist`、`add_tracks`。
- `routers/playlists.py`:`POST /playlists/generate`(讀)、`POST /playlists/save`(寫)。

### 只用可用端點
Search、建立歌單(`POST /users/{id}/playlists`)、加歌(`POST /playlists/{id}/tracks`)
都仍可用;避開被禁的 Recommendations。
注意:此 app 的 search `limit` 上限是 10,要更多用 `offset` 翻頁。

### 重新產生不重複(依相關度往下遞補)
同一句再產生時希望換一批。做法:保留相關度排序,但**排除推薦過的曲目**,
照順位往下取(必要時 offset 翻頁取更深候選)。
- `recommended_track` 表記錄推薦過的 URI;`RecommendationRepository` 存取。
- `generate_playlist(..., exclude_uris=...)` 跳過這些 URI。
- router 在 /generate 時讀歷史排除、產完記錄;`POST /playlists/history/reset` 清空重來。
- 取捨:越往下相關度越低,池子會見底——「完全不重複」與「都很貼題」無法兼得。

## 六、設計模式對照(練習目標)

- **Repository pattern** — 聽歌統計的資料存取(Day 3)
- **Strategy pattern** — 依曲風分流的搜尋策略(Day 5)
- **Adapter pattern** — 多來源演唱會資料轉統一格式(Day 8)
- **分層架構** — 全專案
