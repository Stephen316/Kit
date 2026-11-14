from convert.formats.Fusion.BrepCodec.Journal.Attributes.AttribLinks import AttribLinks
from convert.formats.Fusion.BrepCodec.Journal.Attributes.StitchAttrib import (
    StitchAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Attributes.VertedgeAttrib import (
    KVertedgeCap,
    VertedgeAttrib,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.FieldCursor import FieldCursor
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.NeedFieldMut import (
    NeedFieldMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadCountMut import (
    ReadCountMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadDoubleMut import (
    ReadDoubleMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadLongMut import (
    ReadLongMut,
)
from convert.formats.Fusion.BrepCodec.Journal.Reading.Fields.ReadRefMut import (
    ReadRefMut,
)


def ReadSysLinks(Cursor: FieldCursor) -> AttribLinks:
    NeedFieldMut(Cursor, (12, -1))
    NeedFieldMut(Cursor, (4, -1))
    return AttribLinks(ReadRefMut(Cursor), ReadRefMut(Cursor), ReadRefMut(Cursor))


def ReadStitchNode(Cursor: FieldCursor) -> StitchAttrib:
    Links = ReadSysLinks(Cursor)
    return StitchAttrib(
        Links, (ReadDoubleMut(Cursor), ReadDoubleMut(Cursor), ReadDoubleMut(Cursor))
    )


def ReadVertedge(Cursor: FieldCursor) -> VertedgeAttrib:
    Links = ReadSysLinks(Cursor)
    Count = ReadCountMut(Cursor, KVertedgeCap)
    return VertedgeAttrib(
        Links,
        tuple((ReadRefMut(Cursor), ReadLongMut(Cursor)) for _ in range(Count)),
    )
