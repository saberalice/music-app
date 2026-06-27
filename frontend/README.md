# Music App 前端(Vite + React)

## 跑起來

需要先裝好 Node.js(建議用 nvm 裝 LTS)。

```bash
cd frontend
npm install        # 第一次或依賴有變時
npm run dev        # 啟動 dev server,預設 http://127.0.0.1:5173
```

後端也要同時開著(專案根目錄 `./run.sh`,跑在 127.0.0.1:8000)。

## 結構

```
src/
  api.js                  # 集中對後端的呼叫
  App.jsx                 # 入口:判斷登入 → 顯示登入頁或統計頁
  components/StatsPage.jsx # Top Artists + 曲風分佈(Recharts)
  styles.css
```
