from __future__ import annotations

from typing import NotRequired, TypedDict

from convert.Formats.Fusion.EntityCodec.Schema.WireType import KWireKind
from convert.Formats.Fusion.EntityCodec.Vocabulary.FieldJson import FieldJson


# wire json needs an explicit state contract so entity identifiers retain their schema and reference meaning
class WireJson(TypedDict):
    KindValue: KWireKind
    Arguments: NotRequired[list[WireJson]]
    Members: NotRequired[list[FieldJson[WireJson]]]
    ClassGuid: NotRequired[str]
    FixedCount: NotRequired[int]
    AllowedInts: NotRequired[list[int]]
    HasMatrixRows: NotRequired[bool]
