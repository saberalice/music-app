"""把使用者一句話解析成 PlaylistSpec 的商業邏輯。

負責「編排」與「fallback」:呼叫 GeminiClient → 解析 → 出錯時退而求其次。
這是 Day 4 的重點——整合 AI 進服務時,外部 LLM 不可靠(逾時、額度用完、
回傳壞 JSON),不能讓它把整個功能弄崩。
"""

import logging

import httpx

from app.core.config import settings
from app.models.schemas import PlaylistSpec
from app.services.gemini_client import GeminiClient, build_prompt, parse_spec

logger = logging.getLogger(__name__)


def fallback_spec(sentence: str) -> PlaylistSpec:
    """LLM 不可用時的保底:至少把整句當關鍵字,讓下游搜尋還能運作。"""
    return PlaylistSpec(keywords=[sentence])


def parse_context(sentence: str) -> PlaylistSpec:
    """一句話 → 結構化歌單條件。任何失敗都回 fallback,不丟例外給路由。"""
    client = GeminiClient(settings.gemini_api_key, settings.gemini_model)
    try:
        raw = client.generate(build_prompt(sentence))
        return parse_spec(raw)
    except (httpx.HTTPError, ValueError, KeyError, PermissionError) as exc:
        # ValueError 涵蓋 json 解析失敗;KeyError 涵蓋回應結構不如預期。
        # 不靜默吞掉:記下原因,方便診斷(否則 fallback 會讓失敗隱形)。
        logger.warning("Gemini 解析失敗,改用 fallback(句子=%r):%s: %s",
                       sentence, type(exc).__name__, exc)
        return fallback_spec(sentence)
