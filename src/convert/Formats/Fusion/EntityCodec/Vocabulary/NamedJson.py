from typing import TypedDict

from convert.Formats.Fusion.EntityCodec.Vocabulary.WireJson import WireJson


# named json needs an explicit state contract so entity identifiers retain their schema and reference meaning
class NamedJson(TypedDict):
    TypeName: str
    ValueType: WireJson
