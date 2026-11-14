from convert.formats.Fusion.EntityCodec.Frame.NamedShape import KVectorName, NamedShape
from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.NamedMetadata import NamedMetadata
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Values.ReadValueMut import ReadValueMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText


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
