from __future__ import annotations

from vndb_client.models import VndbModel


class ImageBase(VndbModel):
    """Image fields common to all VNDB image objects."""

    id: str
    url: str | None = None
    dims: list[int] | None = None
    sexual: float | None = None
    violence: float | None = None
    votecount: int | None = None


class Image(ImageBase):
    """VN cover image (adds thumbnail fields not present on character images)."""

    thumbnail: str | None = None
    thumbnail_dims: list[int] | None = None
