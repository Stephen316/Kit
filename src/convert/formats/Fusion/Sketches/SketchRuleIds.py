# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.formats.Fusion.HistoryRef import ReadNativeRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs

# sketch roots store separate ordered membership lists for relations and dimensions
KSketchRoot = "44A64366-4BD3-4B24-881A-F94C206E8F2D"


# tagged membership lists cannot use records from outside the owning sketch root
def ReadRuleIds(Cursor: MetaCursor) -> tuple[int, ...]:
    if Cursor.TakeBytes(1) != b"\1":
        raise ValueError("Invalid Fusion sketch relation membership tag")
    Count = Cursor.ReadCount(100000)
    return tuple(ReadNativeRef(Cursor) for _ in range(Count))


# reciprocal membership rejects orphan records even when their backlinks appear valid
def ReadSketchRules(
    BulkData: bytes, RootSpan: RecordSpan
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    Start = RootSpan.PayloadOffset + 4
    if (
        not RootSpan.IsPrimary
        or RootSpan.ClassGuid != KSketchRoot
        or not 0 <= Start <= RootSpan.EndOffset <= len(BulkData)
    ):
        raise ValueError("Invalid Fusion sketch relation root")
    Cursor = MetaCursor(BulkData[Start : RootSpan.EndOffset])
    Props = ReadGeomAttrs(Cursor)
    Genesis = Props.get("EntityGenesis")
    if (
        type(Genesis) is not int
        or Genesis != 2
        or not Cursor.ReadText(True, Maximum=1024)
    ):
        raise ValueError("Unsupported Fusion sketch relation root attributes")
    Cursor.ReadLong()
    Geometric, Dimensions = ReadRuleIds(Cursor), ReadRuleIds(Cursor)
    Combined = Geometric + Dimensions
    Trailer = Cursor.DataValue[Cursor.Offset :]
    if (
        len(set(Combined)) != len(Combined)
        or len(Trailer) < 32
        or Trailer[:10] != bytes(5) + b"\7" + bytes(4)
        or Trailer[-4:] != b"\0\0\1\1"
    ):
        raise ValueError("Invalid Fusion sketch relation membership")
    ReadNativeRef(MetaCursor(Trailer[-15:-4]))
    return Geometric, Dimensions
