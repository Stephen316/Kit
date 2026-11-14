from functools import cache as CacheValue
from json import loads as LoadJson
from lzma import decompress as Decompress
from pathlib import Path as FilePath
from types import MappingProxyType as ReadOnlyMap
from typing import cast as CastValue

from convert.formats.Fusion.EntityCodec.Schema.ClassSchema import ClassSchema
from convert.formats.Fusion.EntityCodec.Schema.NamedType import NamedType
from convert.formats.Fusion.EntityCodec.Vocabulary.CatalogJson import CatalogJson
from convert.formats.Fusion.EntityCodec.Vocabulary.NativeCatalog import NativeCatalog
from convert.formats.Fusion.EntityCodec.Vocabulary.ReadSchema import ReadSchema
from convert.formats.Fusion.EntityCodec.Vocabulary.ReadWireType import ReadWireType


@CacheValue
def ReadCatalog() -> NativeCatalog:
    Source = FilePath(__file__).with_name("NativeClasses.xz")
    Value = CastValue(CatalogJson, LoadJson(Decompress(Source.read_bytes())))
    Grouped: dict[str, tuple[ClassSchema, ...]] = {}
    for Entry in Value["Classes"]:
        Schema = ReadSchema(Entry)
        Identity = Schema.ClassGuid.upper()
        Current = Grouped.get(Identity, ())
        if any(Other.SchemaVersion == Schema.SchemaVersion for Other in Current):
            raise ValueError("Duplicate Fusion native class/version declaration")
        Grouped[Identity] = (*Current, Schema)
    NamedTypes = tuple(
        NamedType(Entry["TypeName"], ReadWireType(Entry["ValueType"]))
        for Entry in Value["NamedTypes"]
    )
    return NativeCatalog(ReadOnlyMap(Grouped), NamedTypes)
