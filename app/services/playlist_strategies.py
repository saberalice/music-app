"""依曲風分流的搜尋策略(Strategy pattern)。

同一個介面 SearchStrategy,不同曲風換不同實作,把 PlaylistSpec 轉成
Spotify Search 查詢字串。要支援新曲風,只要新增一個策略 class,
不用改既有程式——這就是 Strategy pattern 想解決的事。

純邏輯、不碰網路,方便單元測試。
"""

from abc import ABC, abstractmethod

from app.models.schemas import PlaylistSpec


class SearchStrategy(ABC):
    """搜尋策略介面。"""

    name: str = "default"
    market: str | None = None  # Spotify 市場代碼,None 表示不限定

    @abstractmethod
    def build_queries(self, spec: PlaylistSpec) -> list[str]:
        """把歌單條件轉成一串 Spotify Search 查詢。"""


class JpopStrategy(SearchStrategy):
    """日系流行/搖滾:帶日本市場,用歌手與關鍵字搜。"""

    name = "jpop"
    market = "JP"

    def build_queries(self, spec: PlaylistSpec) -> list[str]:
        queries = [f"artist:{a}" for a in spec.seed_artists]
        tag = spec.genre or "j-pop"
        queries += [f"{kw} {tag}" for kw in spec.keywords[:3]]
        return queries or [tag]


class ClassicalStrategy(SearchStrategy):
    """古典:用「作曲家 + 曲式」搜(如 Chopin nocturne)。"""

    name = "classical"

    def build_queries(self, spec: PlaylistSpec) -> list[str]:
        # seed_artists 在古典情境通常是作曲家;keywords 常含曲式(nocturne/sonata)
        forms = spec.keywords[:2]
        queries = []
        for composer in spec.seed_artists:
            if forms:
                queries += [f"{composer} {form}" for form in forms]
            else:
                queries.append(composer)
        return queries or [" ".join(spec.keywords) or "classical"]


class DefaultStrategy(SearchStrategy):
    """通用:genre + mood + 關鍵字組一般查詢。"""

    name = "default"

    def build_queries(self, spec: PlaylistSpec) -> list[str]:
        base = " ".join(p for p in (spec.genre, spec.mood) if p)
        queries = [f"{base} {kw}".strip() for kw in spec.keywords[:3]]
        queries += [f"artist:{a}" for a in spec.seed_artists]
        return queries or [base or "music"]


# 哪些 genre 走哪個策略
_JPOP_GENRES = {"j-pop", "jpop", "j-rock", "jrock", "japanese", "city pop"}


def select_strategy(spec: PlaylistSpec) -> SearchStrategy:
    """依曲風挑策略。新增曲風時在這裡多一個分支即可。"""
    genre = (spec.genre or "").lower()
    if "classical" in genre:
        return ClassicalStrategy()
    if genre in _JPOP_GENRES or "j-pop" in genre or "j-rock" in genre:
        return JpopStrategy()
    return DefaultStrategy()
