"""Day 4 AI 解析測試。

全部不打 Gemini:純函式直接測,fallback 用 monkeypatch 模擬 LLM 失敗。
"""

import httpx
import pytest

from app.services import context_service
from app.services.gemini_client import GeminiClient, build_prompt, parse_spec


def test_build_prompt_contains_sentence():
    prompt = build_prompt("下雨的午後想專心工作的爵士")
    assert "下雨的午後想專心工作的爵士" in prompt
    assert "JSON" in prompt


def test_parse_spec_valid_json():
    raw = '{"genre": "jazz", "mood": "calm", "era": null, "seed_artists": [], "keywords": ["rainy", "focus"]}'
    spec = parse_spec(raw)
    assert spec.genre == "jazz"
    assert spec.mood == "calm"
    assert spec.era is None
    assert spec.keywords == ["rainy", "focus"]


def test_parse_spec_strips_markdown_fences():
    # LLM 有時會把 JSON 包在 ```json ... ``` 裡
    raw = '```json\n{"genre": "rock", "keywords": ["energetic"]}\n```'
    spec = parse_spec(raw)
    assert spec.genre == "rock"
    assert spec.keywords == ["energetic"]


def test_parse_spec_missing_and_null_lists_use_defaults():
    # 缺欄位、list 欄位回 null 都要安全轉成預設
    spec = parse_spec('{"genre": "classical", "seed_artists": null}')
    assert spec.genre == "classical"
    assert spec.seed_artists == []  # null → []
    assert spec.keywords == []  # 缺欄位 → []
    assert spec.mood is None


def test_parse_spec_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_spec("這不是 JSON,只是一段廢話")


def test_parse_context_falls_back_when_llm_fails(monkeypatch):
    # 模擬 Gemini 呼叫丟錯 → parse_context 應回 fallback(整句當關鍵字),不丟例外
    def boom(self, prompt):
        raise httpx.HTTPError("LLM down")

    monkeypatch.setattr(GeminiClient, "generate", boom)
    spec = context_service.parse_context("深夜開車想聽 city pop")
    assert spec.keywords == ["深夜開車想聽 city pop"]
    assert spec.genre is None
