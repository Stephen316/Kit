from json import loads as ReadJson
from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.formats.Fusion.DocumentCodec.Materials.Vocabulary.SchemaData import (
    SchemaData,
)
from convert.formats.Fusion.MaterialCodec.Package.Model.SchemaNode import SchemaNode


def ReadSchemaNode(Value: SchemaData) -> SchemaNode:
    return SchemaNode(
        Value["TagName"],
        tuple((Entry[0], Entry[1]) for Entry in Value["Attributes"]),
        tuple(ReadSchemaNode(Child) for Child in Value["Children"]),
    )


def ReadMatSchema() -> tuple[SchemaNode, ...]:
    Resource = FilePath(__file__).with_name("MaterialSchemas.json")
    Values = CastValue(dict[str, SchemaData], ReadJson(Resource.read_bytes()))
    return tuple(ReadSchemaNode(Value) for Value in Values.values())
