from __future__ import annotations

from vndb_client.models import VndbModel


class QuoteVN(VndbModel):
    id: str
    title: str | None = None


class QuoteCharacter(VndbModel):
    id: str
    name: str | None = None


class Quote(VndbModel):
    id: str
    quote: str | None = None
    score: int | None = None
    vn: QuoteVN | None = None
    character: QuoteCharacter | None = None
