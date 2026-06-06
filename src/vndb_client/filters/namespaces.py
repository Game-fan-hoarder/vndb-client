from __future__ import annotations

from vndb_client.filters.predicate import Field


def field(name: str) -> Field:
    """Build a :class:`Field` for an arbitrary VNDB filter name (escape hatch)."""
    return Field(name)


class _VNFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    lang: Field = Field("lang")
    olang: Field = Field("olang")
    platform: Field = Field("platform")
    length: Field = Field("length")
    released: Field = Field("released")
    rating: Field = Field("rating")
    votecount: Field = Field("votecount")
    has_description: Field = Field("has_description")
    has_anime: Field = Field("has_anime")
    has_screenshot: Field = Field("has_screenshot")
    has_review: Field = Field("has_review")
    devstatus: Field = Field("devstatus")
    tag: Field = Field("tag")
    dtag: Field = Field("dtag")
    anime_id: Field = Field("anime_id")
    label: Field = Field("label")
    release: Field = Field("release")
    character: Field = Field("character")
    staff: Field = Field("staff")
    developer: Field = Field("developer")


class _ReleaseFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    lang: Field = Field("lang")
    platform: Field = Field("platform")
    released: Field = Field("released")
    resolution: Field = Field("resolution")
    resolution_aspect: Field = Field("resolution_aspect")
    minage: Field = Field("minage")
    medium: Field = Field("medium")
    voiced: Field = Field("voiced")
    engine: Field = Field("engine")
    rtype: Field = Field("rtype")
    extlink: Field = Field("extlink")
    drm: Field = Field("drm")
    patch: Field = Field("patch")
    freeware: Field = Field("freeware")
    uncensored: Field = Field("uncensored")
    official: Field = Field("official")
    has_ero: Field = Field("has_ero")
    vn: Field = Field("vn")
    producer: Field = Field("producer")


class _ProducerFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    lang: Field = Field("lang")
    type: Field = Field("type")
    extlink: Field = Field("extlink")


class _CharacterFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    role: Field = Field("role")
    blood_type: Field = Field("blood_type")
    sex: Field = Field("sex")
    sex_spoil: Field = Field("sex_spoil")
    gender: Field = Field("gender")
    gender_spoil: Field = Field("gender_spoil")
    height: Field = Field("height")
    weight: Field = Field("weight")
    bust: Field = Field("bust")
    waist: Field = Field("waist")
    hips: Field = Field("hips")
    cup: Field = Field("cup")
    age: Field = Field("age")
    trait: Field = Field("trait")
    dtrait: Field = Field("dtrait")
    birthday: Field = Field("birthday")
    seiyuu: Field = Field("seiyuu")
    vn: Field = Field("vn")


class _StaffFilters:
    id: Field = Field("id")
    aid: Field = Field("aid")
    search: Field = Field("search")
    lang: Field = Field("lang")
    gender: Field = Field("gender")
    role: Field = Field("role")
    extlink: Field = Field("extlink")
    ismain: Field = Field("ismain")


class _TagFilters:
    id: Field = Field("id")
    search: Field = Field("search")
    category: Field = Field("category")


class _TraitFilters:
    id: Field = Field("id")
    search: Field = Field("search")


class _QuoteFilters:
    id: Field = Field("id")
    vn: Field = Field("vn")
    character: Field = Field("character")
    random: Field = Field("random")


vn_filters = _VNFilters()
release_filters = _ReleaseFilters()
producer_filters = _ProducerFilters()
character_filters = _CharacterFilters()
staff_filters = _StaffFilters()
tag_filters = _TagFilters()
trait_filters = _TraitFilters()
quote_filters = _QuoteFilters()
