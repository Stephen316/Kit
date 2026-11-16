from convert.Formats.Fusion.EntityCodec.Frame.ReadNamedMut import ReadNamedMut
from convert.Formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.Formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.Formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.Formats.Fusion.EntityCodec.Schema.CheckReference import CheckReference
from convert.Formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.Formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.Formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.Formats.Fusion.EntityCodec.Wire.ReadRefMut import ReadRefMut
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText


# the frame operation needs a distinct decoding boundary so entity identifiers retain their schema and reference meaning
def ReadFrameMut(
    Cursor: MetaCursor, IsPrimary: bool, Catalog: EntityCatalog
) -> EntityFrame:
    RootId = Cursor.ReadText(Maximum=KMaxFeatureText)
    if not IsPrimary:
        return EntityFrame(RootId, None, None)
    Subjects: tuple[SubjectValue, ...] | None = None
    if ReadAtomMut(Cursor, WireType("bool")):
        Entries: list[SubjectValue] = []
        for _ in range(Cursor.ReadCount(KMaxCount)):
            Target = ReadRefMut(Cursor)
            CheckReference(Target, "", Catalog)
            ObserverIndex = int(ReadAtomMut(Cursor, WireType("i32")))
            Entries.append(SubjectValue(Target, ObserverIndex))
        Subjects = tuple(Entries)
    Metadata = (
        ReadNamedMut(Cursor, Catalog) if ReadAtomMut(Cursor, WireType("bool")) else None
    )
    return EntityFrame(RootId, Subjects, Metadata)
