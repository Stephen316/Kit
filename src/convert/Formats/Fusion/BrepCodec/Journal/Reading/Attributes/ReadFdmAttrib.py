from convert.Formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.Formats.Fusion.BrepCodec.Journal.Attributes.FeatureAttrib import (
    FeatureAttrib,
    KFeatureFlags,
    KFeatureLayouts,
    KFeatureTypes,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadTextMut import (
    ReadTextMut,
)
from convert.Formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadVectorMut import (
    ReadVectorMut,
)


# the fdm attribute operation needs a distinct decoding boundary so revision ownership survives native history reconstruction
def ReadFdmAttrib(Cursor: FieldCursor, Links: AttribLinks) -> FeatureAttrib:
    NeedFieldMut(Cursor, (4, 2))
    NeedFieldMut(Cursor, (4, 2))
    DataName = ReadTextMut(Cursor)
    if DataName not in KFeatureLayouts:
        raise ValueError("Unsupported Fusion feature attribute data")
    NeedFieldMut(Cursor, (4, 3))
    FeatureTag = ReadLongMut(Cursor)
    NeedFieldMut(Cursor, (4, KFeatureFlags))
    NeedFieldMut(Cursor, (4, KFeatureLayouts[DataName]))
    TypeCode = KFeatureTypes[DataName]
    NeedFieldMut(Cursor, (4, TypeCode))
    if DataName == "feature_data":
        return FeatureAttrib(Links, DataName, FeatureTag, KFeatureFlags, TypeCode)
    Points = tuple(ReadVectorMut(Cursor, 19) for _ in range(3))
    TailCode = ReadLongMut(Cursor)
    if TailCode not in (0, 1):
        raise ValueError("Unsupported Fusion feature attribute data")
    return FeatureAttrib(
        Links, DataName, FeatureTag, KFeatureFlags, TypeCode, Points, TailCode
    )
