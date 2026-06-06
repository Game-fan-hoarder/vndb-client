from __future__ import annotations

from vndb_client.entities.common import ImageBase
from vndb_client.models import VndbModel


class Character(VndbModel):
    id: str
    name: str | None = None
    original: str | None = None
    aliases: list[str] | None = None
    description: str | None = None
    blood_type: str | None = None
    height: int | None = None
    weight: int | None = None
    bust: int | None = None
    waist: int | None = None
    hips: int | None = None
    cup: str | None = None
    age: int | None = None
    birthday: list[int] | None = None
    sex: list[str | None] | None = None
    gender: list[str | None] | None = None
    image: ImageBase | None = None
