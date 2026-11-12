from enum import StrEnum
from typing import cast as CastValue

from convert.formats.Fusion.MetaCursor import MetaCursor


# the same native index grammar serves three typed segment headers
class SegmentKind(StrEnum):
    KDesign = "FusionDesignSegmentType"
    KBrowser = "FusionBrowserSegmentType"
    KAct = "FusionACTSegmentType"


# each auxiliary segment declares a fixed index and storage kind in version eight
KSegmentLayout = {
    SegmentKind.KDesign: (None, (1, 0)),
    SegmentKind.KBrowser: (2, (6, 0)),
    SegmentKind.KAct: (1, (5, 0)),
}


# an expected segment kind prevents an unrelated index from validating this stream pair
def CheckMetaHeader(Cursor: MetaCursor, Segment: SegmentKind) -> None:
    if not isinstance(CastValue(object, Segment), SegmentKind):
        raise ValueError("Unsupported Fusion MetaStream segment kind")
    KindValue = Cursor.ReadText()
    SegmentId, _ = Cursor.ReadWord(), Cursor.ReadText(True)
    Magic, Version, _, _ = (Cursor.ReadWord() for _ in range(4))
    Repeated, _ = Cursor.ReadText(), Cursor.ReadText()
    Storage = Cursor.ReadWord(), Cursor.ReadWord()
    IndexValue, StorageValue = KSegmentLayout[Segment]
    if (
        KindValue != Segment.value
        or Repeated != KindValue
        or Magic != 1234
        or Version != 8
        or Storage != StorageValue
        or (IndexValue is not None and SegmentId != IndexValue)
    ):
        if Segment is SegmentKind.KDesign:
            raise ValueError("Unsupported Fusion design MetaStream")
        raise ValueError(f"Unsupported Fusion {Segment.value} MetaStream")


# capture registry ownership so bulk headers cannot assign their own record classes
def ReadMetaIndex(
    MetaData: bytes,
    *,
    Segment: SegmentKind = SegmentKind.KDesign,
) -> tuple[
    dict[int, tuple[str, str, str]],
    dict[int, int],
    list[tuple[int, int, bool]],
]:
    Cursor = MetaCursor(MetaData)
    CheckMetaHeader(Cursor, Segment)

    Classes, Owners = ReadMetaKeysMut(Cursor)
    _ = Cursor.TakeBytes(8 * Cursor.ReadCount(1000000))
    Entries: list[tuple[int, int, bool]] = []
    PrimaryIds: set[int] = set()
    for IsPrimary in (True, False):
        for _ in range(Cursor.ReadCount(1000000)):
            Identity, Offset = Cursor.ReadLong(), Cursor.ReadLong()
            if Identity not in Owners or (IsPrimary and Identity in PrimaryIds):
                raise ValueError("Fusion index and class registry disagree")
            if IsPrimary:
                PrimaryIds.add(Identity)
            Entries.append((Offset, Identity, IsPrimary))
    NextId, _ = Cursor.ReadLong(), Cursor.ReadWord()
    if PrimaryIds != Owners.keys() or (Owners and NextId <= max(Owners)):
        raise ValueError("Invalid Fusion primary identity index")
    Properties: set[str] = set()
    for _ in range(Cursor.ReadCount(1024)):
        NameValue, _ = Cursor.ReadText(), Cursor.ReadWord()
        if NameValue in Properties:
            raise ValueError("Duplicate Fusion metadata property")
        Properties.add(NameValue)
    if Cursor.Offset != len(MetaData):
        raise ValueError("Trailing Fusion MetaStream data")
    return Classes, Owners, Entries


# class ownership must be complete before validating indexed object offsets
def ReadMetaKeysMut(
    Cursor: MetaCursor,
) -> tuple[dict[int, tuple[str, str, str]], dict[int, int]]:
    Classes: dict[int, tuple[str, str, str]] = {}
    Owners: dict[int, int] = {}
    KnownGuids: set[str] = set()
    for CodeValue in range(256, 256 + Cursor.ReadCount(100000)):
        ClassGuid, BaseGuid = Cursor.ReadText(), Cursor.ReadText()
        _ = Cursor.ReadWord()
        ClassSpace = Cursor.ReadText()
        if not ClassGuid or ClassGuid in KnownGuids:
            raise ValueError("Missing or duplicate Fusion class GUID")
        KnownGuids.add(ClassGuid)
        Classes[CodeValue] = ClassGuid, BaseGuid, ClassSpace
        for _ in range(Cursor.ReadCount(1000000)):
            Identity = Cursor.ReadLong()
            if Identity in Owners:
                raise ValueError("Duplicate primary Fusion object identity")
            Owners[Identity] = CodeValue
    return Classes, Owners
