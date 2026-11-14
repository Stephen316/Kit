from typing import TypedDict

from convert.formats.Fusion.EntityCodec.Vocabulary.NamedJson import NamedJson
from convert.formats.Fusion.EntityCodec.Vocabulary.SchemaJson import SchemaJson


class CatalogJson(TypedDict):
    Classes: list[SchemaJson]
    NamedTypes: list[NamedJson]
