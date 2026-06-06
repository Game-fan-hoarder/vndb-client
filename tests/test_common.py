from __future__ import annotations

from vndb_client.entities.common import Image, ImageBase
from vndb_client.entities.vn import VN
from vndb_client.fields import field_spec


def test_imagebase_parses_without_thumbnail():
    img = ImageBase.model_validate({
        "id": "ch1",
        "url": "https://x/1.jpg",
        "dims": [256, 300],
        "sexual": 0.0,
        "violence": 0.0,
        "votecount": 3,
    })
    assert img.id == "ch1"
    assert img.dims == [256, 300]


def test_image_parses_with_thumbnail():
    img = Image.model_validate({
        "id": "cv1",
        "url": "https://x/1.jpg",
        "thumbnail": "https://x/t.jpg",
        "thumbnail_dims": [128, 150],
    })
    assert img.thumbnail == "https://x/t.jpg"
    assert img.thumbnail_dims == [128, 150]


def test_field_spec_image_includes_thumbnail():
    assert "thumbnail" in field_spec(Image).split(",")


def test_field_spec_imagebase_excludes_thumbnail():
    assert "thumbnail" not in field_spec(ImageBase).split(",")


def test_vn_field_spec_includes_image_thumbnail():
    assert "image.thumbnail" in field_spec(VN).split(",")
