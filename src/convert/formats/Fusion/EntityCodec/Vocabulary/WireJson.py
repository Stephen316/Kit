from __future__ import annotations

from typing import NotRequired, TypedDict

from convert.formats.Fusion.EntityCodec.Schema.WireType import KWireKind
from convert.formats.Fusion.EntityCodec.Vocabulary.FieldJson import FieldJson


class WireJson(TypedDict):
    KindValue: KWireKind
    Arguments: NotRequired[list[WireJson]]
    Members: NotRequired[list[FieldJson[WireJson]]]
    ClassGuid: NotRequired[str]
    FixedCount: NotRequired[int]
    AllowedInts: NotRequired[list[int]]
    HasMatrixRows: NotRequired[bool]
