from functools import cache as CacheValue
from pathlib import Path

from convert.Formats.Fusion.DocumentCodec.Records.ReadDocSchemas import ReadDocSchemas
from convert.Formats.Fusion.DocumentCodec.Vocabulary.ReadVocabulary import (
    ReadVocabulary,
)
from convert.Formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema


# the draw schemas operation needs a distinct decoding boundary so drawing members retain their sheet and model associations
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
