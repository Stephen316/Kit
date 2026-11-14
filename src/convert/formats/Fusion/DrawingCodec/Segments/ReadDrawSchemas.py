from functools import cache as CacheValue
from pathlib import Path

from convert.formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema


@CacheValue
def ReadDrawSchemas() -> tuple[ClassSchema, ...]:
    Catalog: dict[tuple[str, int], ClassSchema] = {}
    Drawing = tuple(
        Entry.Value
        for Entry in ReadVocabulary(Path(__file__).with_name("DrawingClasses.json"))
    )
    for Schema in ReadDocSchemas() + Drawing:
        KeyValue = (Schema.ClassGuid.upper(), Schema.SchemaVersion)
        Previous = Catalog.get(KeyValue)
        if Previous is not None and Previous != Schema:
            raise ValueError("Conflicting Fusion drawing schema vocabulary")
        Catalog[KeyValue] = Schema
    return tuple(Catalog.values())
