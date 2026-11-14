from typing import TypedDict

from convert.formats.Fusion.EntityCodec.Vocabulary.FieldJson import FieldJson
from convert.formats.Fusion.EntityCodec.Vocabulary.WireJson import WireJson


class SchemaJson(TypedDict):
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    Members: list[FieldJson[WireJson]]
    IsValue: bool
