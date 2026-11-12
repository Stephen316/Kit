from convert.formats.Fusion.Assembly.Edits.AsmEditIndex import AsmEditIndex
from convert.formats.Fusion.Assembly.Edits.AsmEditOccur import HasSameMatrix
from convert.formats.Fusion.Assembly.OccurTransform import ReadOccurMatrix
from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.SelectionProxy import SelectCursor

# typed links connect both context frames to the local parent definition
KCopyFrameLink = "549FBB80-B890-473E-A5C0-415D3D9BF4E6"


# shared context markers distinguish linked source and empty target modes
def CheckCopyLink(Cursor: MetaCursor, Populated: bool) -> None:
    if (
        Cursor.TakeBytes(14) != bytes(14)
        or Cursor.TakeBytes(1) != b"\3"
        or Cursor.ReadWord() != int(Populated)
        or (Populated and Cursor.ReadWord() != 1)
        or Cursor.TakeBytes(2) != b"\1\2"
        or Cursor.TakeBytes(8) != bytes(8)
        or Cursor.TakeBytes(5) != b"\1\1\0\0\0"
    ):
        raise ValueError("Unsupported Fusion copy context link framing")


# reciprocal link layouts prove the copied definition stays under the same parent
def ReadCopyLinks(
    BulkData: bytes,
    IndexValue: AsmEditIndex,
    SourceLink: int,
    TargetLink: int,
    Matrix: tuple[float, ...],
) -> tuple[int, int]:
    Owners = IndexValue.Owners
    Source = SelectCursor(BulkData, Owners, SourceLink, KCopyFrameLink)
    CheckCopyLink(Source, True)
    ComponentId = ReadNativeRef(Source)
    if Source.TakeBytes(10) != b"\0\0\0\0\1\0\0\0\1\0":
        raise ValueError("Unsupported Fusion copy source context snapshot marker")
    SnapshotId = ReadNativeRef(Source)
    if (
        Source.DataValue[Source.Offset : Source.Offset + 1] != bytes(1)
        or not HasSameMatrix(Matrix, ReadOccurMatrix(Source))
        or Source.Offset != len(Source.DataValue)
    ):
        raise ValueError("Fusion copy source context link matrix disagrees")
    Target = SelectCursor(BulkData, Owners, TargetLink, KCopyFrameLink)
    CheckCopyLink(Target, False)
    if (
        ReadNativeRef(Target) != ComponentId
        or Target.TakeBytes(8) != b"\xff" * 4 + bytes(4)
        or Target.Offset != len(Target.DataValue)
    ):
        raise ValueError("Fusion copy target context link owner disagrees")
    return ComponentId, SnapshotId
