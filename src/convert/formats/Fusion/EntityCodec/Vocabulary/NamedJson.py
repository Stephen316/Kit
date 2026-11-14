from typing import TypedDict

from convert.formats.Fusion.EntityCodec.Vocabulary.WireJson import WireJson


class NamedJson(TypedDict):
    TypeName: str
    ValueType: WireJson
