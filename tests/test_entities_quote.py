from __future__ import annotations

from vndb_client.entities.quote import Quote, QuoteCharacter, QuoteVN


def test_quote_parses_with_nested_refs():
    q = Quote.model_validate({
        "id": "q1",
        "quote": "...",
        "score": 42,
        "vn": {"id": "v17", "title": "Ever17"},
        "character": {"id": "c1", "name": "Tsugumi"},
    })
    assert q.id == "q1"
    assert q.score == 42
    assert isinstance(q.vn, QuoteVN)
    assert q.vn.title == "Ever17"
    assert isinstance(q.character, QuoteCharacter)
    assert q.character.name == "Tsugumi"
