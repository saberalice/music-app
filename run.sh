#!/usr/bin/env bash
# 一鍵啟動後端開發伺服器。
# 用法:在專案根目錄執行 `bash run.sh`(或 `./run.sh`)。
# 停止:Ctrl+C。
#
# 這裡會主動 source conda,所以不管是互動或非互動 shell 都能跑。

set -e  # 任何一步失敗就停,不要帶錯往下跑

# 載入 conda 並啟用本專案環境
source "$HOME/miniconda3/etc/profile.d/conda.sh"
conda activate musicapp

# 切到腳本所在目錄(就算從別處呼叫也能正確執行)
cd "$(dirname "$0")"

# 啟動:綁 127.0.0.1:8000(符合 Spotify redirect URI),--reload 改 code 自動重啟
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
