from typing import TypedDict

from convert.formats.Fusion.EntityCodec.Vocabulary.FieldJson import FieldJson
from convert.formats.Fusion.EntityCodec.Vocabulary.WireJson import WireJson


# schema json needs an explicit state contract so entity identifiers retain their schema and reference meaning
class SchemaJson(TypedDict):
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    Members: list[FieldJson[WireJson]]
    IsValue: bool
