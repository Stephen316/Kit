from convert.Formats.Fusion.EntityCodec.Frame.NamedShape import KVectorName, NamedShape
from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Values.ReadValueMut import ReadValueMut
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText


# the named operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadNamedMut(
    Cursor: MetaCursor, Catalog: EntityCatalog
) -> tuple[NamedMetadata, ...]:
    Entries: list[NamedMetadata] = []
    Names: set[str] = set()
    for _ in range(Cursor.ReadCount(KMaxCount)):
        FieldName = Cursor.ReadText(Maximum=KMaxFeatureText)
        TypeName = Cursor.ReadText(Maximum=KMaxFeatureText)
        ElementName = (
            Cursor.ReadText(Maximum=KMaxFeatureText) if TypeName == KVectorName else ""
        )
        if FieldName in Names:
            raise ValueError("Duplicate or unsupported Fusion entity named metadata")
        Shape = NamedShape(TypeName, ElementName, Catalog)
        Names.add(FieldName)
        Entries.append(
            NamedMetadata(
                FieldName, TypeName, ReadValueMut(Cursor, Shape, Catalog), ElementName
            )
        )
    return tuple(Entries)
