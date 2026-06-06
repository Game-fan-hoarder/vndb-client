from __future__ import annotations

from vndb_client.models import VndbModel


class ReleaseLang(VndbModel):
    lang: str
    title: str | None = None
    latin: str | None = None
    mtl: bool | None = None
    main: bool | None = None


class ReleaseMedia(VndbModel):
    medium: str | None = None
    qty: int | None = None


class Release(VndbModel):
    id: str
    title: str | None = None
    alttitle: str | None = None
    released: str | None = None
    platforms: list[str] | None = None
    minage: int | None = None
    patch: bool | None = None
    freeware: bool | None = None
    uncensored: bool | None = None
    official: bool | None = None
    has_ero: bool | None = None
    resolution: list[int] | str | None = None
    engine: str | None = None
    voiced: int | None = None
    notes: str | None = None
    gtin: str | None = None
    catalog: str | None = None
    languages: list[ReleaseLang] | None = None
    media: list[ReleaseMedia] | None = None
