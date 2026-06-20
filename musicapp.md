# 音樂 App ・ 10 天開發計畫

> 目標:用 **Python (FastAPI) + React** 做出一個你自己天天會用的音樂 app,
> 包含三大功能:① 聽歌統計 ② AI 歌單產生器 ③ 演唱會 / 音樂會通知。
> 過程中刻意練到後端核心概念、設計模式,以及「會用 AI 工具但不盲信」的開發紀律。

---

## 使用說明

- 每天的任務分成「**核心任務**(必做)」與「**進階**(行有餘力)」。進度落後時先砍進階,別砍核心。
- 每天都要做的三個習慣(這比寫完功能更重要):
  1. **先想再寫**:動手前先在 `docs/` 寫兩三行,說明這段要做什麼、存什麼、有哪些 API。
  2. **AI 寫完自己逐行讀懂**:讓 AI 產生程式碼,但每一段都要看懂、能解釋,再 commit。看不懂的就問 AI「為什麼這樣寫」。
  3. **小步 commit**:每完成一個小功能就 `git commit`,訊息寫清楚做了什麼。
- 每天結束時把當天的 ✅ 勾起來,順手記一句「今天卡在哪、怎麼解的」——這就是未來面試最好的素材。

---

## 行前準備(Day 1 之前或當天一起做)

- [ ] 安裝 Python 3.12+、Node.js、Git
- [ ] 選一個 AI 編輯器:Cursor / VS Code + Copilot / Claude Code 擇一,先跑通
- [ ] 註冊 [Spotify for Developers](https://developer.spotify.com/),建立一個 App,記下 Client ID / Secret,設定 Redirect URI(先用 `http://localhost:8000/callback`)
- [ ] 申請 [Google AI Studio](https://aistudio.google.com/) 的 Gemini 免費 API key
- [ ] (演唱會功能用)申請 [Bandsintown](https://www.bandsintown.com/api/overview) 或 [Songkick](https://www.songkick.com/developer) API key;台灣場次或古典音樂會則改用爬蟲(見 Day 8)

---

## 第一批:打地基(Day 1)

### Day 1 — 專案骨架與設計

**核心任務**
- [ ] 建立 Git repo,規劃分層目錄結構:
  ```
  app/
    routers/      # API 路由(對外端點)
    services/     # 商業邏輯
    repositories/ # 資料存取
    models/       # 資料結構 (Pydantic / ORM)
    core/         # 設定、共用工具
  docs/           # 設計文件
  tests/
  ```
- [ ] 寫一份簡短的設計文件 `docs/design.md`:這個 app 要存什麼資料、有哪些主要 API、三大功能各自的資料流
- [ ] 用 FastAPI 跑出第一個 `/health` 端點,打開自動產生的 `/docs` 看互動式 API 文件
- [ ] 為 AI 工具建立 context 檔(Cursor 的 `.cursorrules` 或 Claude Code 的 `CLAUDE.md`),寫下專案技術棧、命名規則、目錄結構,讓 AI 產生的碼更貼合你的專案

**進階**
- [ ] 設定環境變數管理(`.env` + `pydantic-settings`),把 API key 從程式碼裡抽出來

**學到的概念**:分層架構(關注點分離)、為什麼 secret 不能寫死在程式碼裡(資安基本功)

---

## 第二批:Spotify 串接與聽歌統計(Day 2–3)

### Day 2 — Spotify OAuth 登入

**核心任務**
- [ ] 實作 Spotify 的 Authorization Code OAuth 流程:導向授權 → 接 callback → 換取 access / refresh token
- [ ] 把 token 安全存起來,做一個 `/me` 端點驗證能拿到你的個人資料
- [ ] 處理 token 過期:用 refresh token 自動換新

**學到的概念**:OAuth 2.0 授權流程(進趨勢後處理認證授權會天天碰到)、token 生命週期管理

> ⚠️ 提醒:Spotify 在 2024/11 之後,新 app **不能用** Recommendations、Audio Features 等端點(會回 403)。
> 本計畫已全程避開,只用仍可用的端點:Search、Top Tracks/Artists、Recently Played、已收藏、建立歌單。

### Day 3 — 抓聽歌資料 + 統計

**核心任務**
- [ ] 抓你的 Top Tracks / Top Artists / 最近播放
- [ ] 設計 SQLite 資料表(歌曲、歌手、播放紀錄),寫 Repository 層負責讀寫(不要讓路由直接碰資料庫)
- [ ] 做統計端點:最常聽的曲風分佈、最常聽的歌手 Top 10
- [ ] 用 AI 幫你寫 1–2 個資料轉換的單元測試,自己讀懂後留下

**進階**
- [ ] 加一個「聽歌時段熱力圖」的資料端點(按星期 × 小時統計)

**學到的概念**:Repository pattern(資料存取與商業邏輯分離)、資料庫 schema 設計、ORM 基礎

---

## 第三批:AI 歌單產生器(Day 4–5)

### Day 4 — LLM 解析情境

**核心任務**
- [ ] 串接 Gemini 免費 API
- [ ] 設計 prompt,讓 LLM 把使用者的一句話(例:「下雨的午後、想專心工作的爵士」)轉成**結構化 JSON**:
  ```json
  { "genre": "jazz", "mood": "calm", "era": null,
    "seed_artists": [], "keywords": ["rainy", "focus", "instrumental"] }
  ```
- [ ] 重點:在 prompt 明確要求「只回傳 JSON、不要任何多餘文字」,後端用 try/except 安全解析,解析失敗時有 fallback

**學到的概念**:把 AI 整合進服務的完整流程、處理 LLM 的非結構化輸出、錯誤處理與 fallback(這正是 HR 說的「AI 工具在開發流程中的實際應用」)

### Day 5 — 依曲風分流 + 組歌單

**核心任務**
- [ ] 定義一個共同介面 `SearchStrategy`,底下做不同實作:`JpopStrategy`、`ClassicalStrategy`、`DefaultStrategy`
- [ ] 每個策略把 Day 4 的 JSON 轉成對應的 Spotify Search 查詢(日文流行帶日本市場參數;古典用作曲家/曲式去搜,如 `Chopin nocturne`)
- [ ] 用 Search 結果組出歌單,做 `POST /playlists/generate` 端點
- [ ] 加一個「存到我的 Spotify」功能:呼叫建立歌單 + 加歌 API

**學到的概念**:**Strategy pattern**(同一介面、不同曲風換不同實作)——這是設計模式最好懂的入門範例,你會親身體會「為什麼要用它」

---

## 第四批:前端,讓它變成真的 app(Day 6–7)

### Day 6 — React 基礎 + 登入與統計頁

**核心任務**
- [ ] 建立 React 專案(Vite),跑通與 FastAPI 後端的串接(注意 CORS 設定)
- [ ] 做 Spotify 登入按鈕 → 走完 OAuth → 回到前端
- [ ] 做「聽歌統計」頁:把 Day 3 的統計端點視覺化(用 Recharts 之類的圖表庫)

**學到的概念**:前後端分離、CORS、前端如何呼叫 API

> 💡 若時間吃緊或想先求有:可改用 **Streamlit** 純 Python 快速生介面,幾小時就有成品。
> 但若你想完整練前端,建議照計畫用 React,這也更接近趨勢這類公司的架構。

### Day 7 — 歌單產生器 UI

**核心任務**
- [ ] 做輸入框:使用者打一句話 → 呼叫 `/playlists/generate` → 顯示產生的歌單
- [ ] 每首歌顯示封面、歌名、歌手,放「在 Spotify 開啟」連結
- [ ] 加「存到我的 Spotify」按鈕
- [ ] 處理載入中狀態與錯誤提示(網路慢、LLM 回傳異常時不要白畫面)

**進階**
- [ ] 讓使用者能在產生後微調(刪掉不喜歡的歌、重新產生)

**學到的概念**:處理非同步請求、loading / error 狀態管理、好的使用者體驗細節

---

## 第五批:演唱會 / 音樂會通知(Day 8–9)

### Day 8 — 多來源整合(這段最像真實後端系統)

**核心任務**
- [ ] 定義共同介面 `ConcertSource` 與統一的 `Event` 資料結構(時間、地點、表演者、連結)
- [ ] 實作兩個來源,各自把長相不同的外部資料「轉接」成統一的 `Event`:
  - `JpopArtistSource`:從你 Spotify 的「已追蹤歌手 / Top Artists」拿名單,查 Bandsintown / Songkick(或台灣售票平台爬蟲)
  - `ClassicalVenueSource`:抓國家音樂廳節目。**沒有官方 API**,資料在 OPENTIX(`opentix.life/o/ntch`),需用爬蟲;先打開瀏覽器 Network 分頁,找它前端實際呼叫的 JSON 端點會比直接解析 HTML 省事
- [ ] 通知模組只依賴 `ConcertSource` 介面,完全不需要知道資料從哪來

**學到的概念**:**Adapter pattern**(把不同格式的外部資料轉成統一介面)、面對「沒有官方 API」的真實情境

> ⚠️ 爬蟲務必看對方的 robots.txt 與服務條款、放慢請求頻率;若對方明確禁止就改用有官方 API 的來源。
> 「尊重對方系統」是底線,進資安公司後你會更理解為什麼。

### Day 9 — 排程、去重、通知

**核心任務**
- [ ] 用 APScheduler 定時輪詢各來源
- [ ] 在資料庫記錄「已通知過的場次」,避免重複通知(去重邏輯)
- [ ] 接一個通知管道:Email(SMTP)或 Line Notify
- [ ] 前端做一頁:顯示近期場次、管理追蹤的歌手 / 是否訂閱古典音樂會

**學到的概念**:排程任務、狀態管理與去重、事件驅動的通知設計

---

## 第六批:收尾(Day 10）

### Day 10 — 測試、部署、文件

**核心任務**
- [ ] 用 pytest 補幾個關鍵路徑的測試(OAuth token 刷新、LLM 解析 fallback、去重邏輯)
- [ ] 全面檢查錯誤處理:外部 API 掛掉、額度用完、網路逾時時不會整個崩潰
- [ ] 寫 `README.md`:專案介紹、架構圖、如何在本機跑起來、用到哪些設計模式(這是給未來的你和面試官看的)
- [ ] 部署:後端上 Render / Railway / Fly.io,前端上 Vercel / Netlify,讓它變成真的能用的 app

**進階**
- [ ] 寫一篇簡短的開發心得,記錄你用 AI 工具的方式、踩過的坑——這是很好的作品集素材

---

## 整體進度表

| 批次 | 天數 | 產出 |
|------|------|------|
| 一・地基 | Day 1 | 專案骨架 + 設計文件 + AI 工具設定 |
| 二・Spotify | Day 2–3 | OAuth 登入 + 聽歌統計 API |
| 三・AI 歌單 | Day 4–5 | LLM 解析 + 歌單產生(Strategy pattern) |
| 四・前端 | Day 6–7 | 可登入、看統計、產生歌單的網頁 |
| 五・通知 | Day 8–9 | 多來源演唱會 / 音樂會通知(Adapter pattern) |
| 六・收尾 | Day 10 | 測試 + 部署 + 文件 |

## 如果進度落後怎麼辦(優先順序)

1. **核心 MVP(絕對要完成)**:Day 1–5 + Day 6。也就是「能登入、看統計、用 AI 產生歌單並存回 Spotify」——這本身就是完整、能展示的作品。
2. 前端來不及做精美 → 先用 Streamlit 把功能跑通,之後再換 React。
3. **演唱會通知(Day 8–9)當作 stretch goal**:它最能練系統設計,但也最花時間。做不完不影響核心成果,可入職後再補。

## 涵蓋到的能力盤點(對照你想準備的清單)

- 後端:FastAPI、REST API 設計、資料庫 schema、ORM
- 設計模式:Repository、Strategy、Adapter、分層架構
- AI 整合:LLM 串接、結構化輸出、prompt 設計、fallback
- 工程實務:Git 流程、OAuth、排程、測試、部署
- AI 工具使用紀律:讓 AI 產生 → 自己逐行讀懂 → 補測試 → 才 commit
