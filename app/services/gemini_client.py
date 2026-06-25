"""用 httpx 直接打 Gemini REST API,把一句話解析成歌單條件。

刻意不裝官方 SDK,讓「跟 LLM API 溝通」的細節攤開來看:
  POST .../models/{model}:generateContent?key=...
  body 帶 prompt;用 responseMimeType 要求只回 JSON。

解析相關都拆成 module 層級純函式(build_prompt / extract_text / parse_spec),
不依賴網路,方便單元測試。實際 HTTP 在 GeminiClient。
"""

import json

import httpx

from app.models.schemas import PlaylistSpec

API_BASE = "https://generativelanguage.googleapis.com/v1beta"

# prompt 明確要求「只回 JSON、不要多餘文字」,並規範欄位與「不確定就填 null」,
# 避免 LLM 亂編。{sentence} 之後代入使用者句子。
PROMPT_TEMPLATE = """你是一個音樂歌單條件解析器。使用者會用一句話描述想聽的音樂情境,
請解析成固定格式的 JSON。

規則:
- 只回傳 JSON,不要任何說明文字或 markdown 圍欄。
- 欄位:
  - genre: 主要曲風(英文小寫,如 "jazz"、"j-pop"、"classical"),無法判斷填 null
  - mood: 情緒/氛圍(英文小寫,如 "calm"、"energetic"、"melancholic"),無法判斷填 null
  - era: 年代(如 "80s"、"90s"、"2010s"),沒提到填 null
  - seed_artists: 句子中明確提到的歌手名(陣列,保留原文),沒有填 []
  - keywords: 3-6 個有助於搜尋的英文關鍵字(陣列)
- 不確定的欄位用 null 或空陣列,不要亂編。

使用者句子:「{sentence}」"""


def build_prompt(sentence: str) -> str:
    """把使用者句子代入 prompt 範本。"""
    return PROMPT_TEMPLATE.format(sentence=sentence)


def extract_text(response_json: dict) -> str:
    """從 Gemini 回應結構中取出模型產生的文字。"""
    return response_json["candidates"][0]["content"]["parts"][0]["text"]


def parse_spec(raw_text: str) -> PlaylistSpec:
    """把模型回的文字解析成 PlaylistSpec(容錯)。

    - 去掉可能夾帶的 ```json ... ``` 圍欄
    - 缺欄位用預設值,list 欄位若回 null 也轉成 []
    - 解析失敗丟 ValueError,交給上層 fallback
    """
    text = raw_text.strip()
    if text.startswith("```"):
        # 去掉第一行(```json)與最後的 ```
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]) if len(lines) >= 2 else text.strip("`")
    data = json.loads(text)  # 壞 JSON 會丟 json.JSONDecodeError(屬 ValueError)
    return PlaylistSpec(
        genre=data.get("genre"),
        mood=data.get("mood"),
        era=data.get("era"),
        seed_artists=data.get("seed_artists") or [],
        keywords=data.get("keywords") or [],
    )


class GeminiClient:
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model

    def generate(self, prompt: str) -> str:
        """送 prompt 給 Gemini,回傳模型產生的純文字。失敗會丟例外。"""
        if not self._api_key:
            raise PermissionError("未設定 GEMINI_API_KEY")
        resp = httpx.post(
            f"{API_BASE}/models/{self._model}:generateContent",
            params={"key": self._api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,  # 解析任務要穩定,溫度調低
                    "responseMimeType": "application/json",
                    # 2.5-flash 預設會「思考」,對這種小任務多餘且偶爾吃光 token
                    # 預算導致沒有輸出 → 關掉,又快又穩
                    "thinkingConfig": {"thinkingBudget": 0},
                },
            },
            timeout=20,
        )
        resp.raise_for_status()
        return extract_text(resp.json())
