from typing import TypedDict

from tests.Convert.Formats.FusionCodec.Entities.FieldJson import FieldJson
from tests.Convert.Formats.FusionCodec.Entities.WireJson import WireJson


# the class json boundary needs grouped coverage so repository automation cannot silently change its observable contract
class ClassJson(TypedDict):
    ClassGuid: str
    BaseGuid: str
    SchemaVersion: int
    Members: list[FieldJson[WireJson]]
    IsValue: bool
