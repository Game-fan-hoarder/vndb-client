from __future__ import annotations

from vndb_client.entities.producer import Producer, ProducerType


def test_producer_parses_and_mirror_compares():
    p = Producer.model_validate({
        "id": "p1",
        "name": "KID",
        "original": None,
        "aliases": ["Kid"],
        "lang": "ja",
        "type": "co",
        "description": None,
    })
    assert p.id == "p1"
    assert p.name == "KID"
    assert p.type == "co"
    assert p.type == ProducerType.CO
