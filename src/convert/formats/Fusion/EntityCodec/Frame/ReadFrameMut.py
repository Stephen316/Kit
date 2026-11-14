from convert.formats.Fusion.EntityCodec.Frame.ReadNamedMut import ReadNamedMut
from convert.formats.Fusion.EntityCodec.Limits import KMaxCount
from convert.formats.Fusion.EntityCodec.Model.EntityFrame import EntityFrame
from convert.formats.Fusion.EntityCodec.Model.SubjectValue import SubjectValue
from convert.formats.Fusion.EntityCodec.Schema.CheckReference import CheckReference
from convert.formats.Fusion.EntityCodec.Schema.EntityCatalog import EntityCatalog
from convert.formats.Fusion.EntityCodec.Schema.WireType import WireType
from convert.formats.Fusion.EntityCodec.Wire.ReadAtomMut import ReadAtomMut
from convert.formats.Fusion.EntityCodec.Wire.ReadRefMut import ReadRefMut
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SegmentCodec.Features.FeatureLimits import KMaxFeatureText


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
