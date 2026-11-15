from typing import TypedDict

from convert.formats.Fusion.EntityCodec.Vocabulary.NamedJson import NamedJson
from convert.formats.Fusion.EntityCodec.Vocabulary.SchemaJson import SchemaJson


# catalog json needs an explicit state contract so entity identifiers retain their schema and reference meaning
class CatalogJson(TypedDict):
    Classes: list[SchemaJson]
    NamedTypes: list[NamedJson]
