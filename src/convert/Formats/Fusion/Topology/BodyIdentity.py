from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SelectionProxy import SelectCursor
from convert.Formats.Fusion.SelectionRef import ReadSelectUuid
from convert.Formats.Fusion.Sketches.GeometryAttrs import ReadGeomAttrs
from convert.Formats.Fusion.Topology.BodyAnchor import KBodyGuid


# a typed body must repeat the anchor identity before an input can select it
def CheckBodyGuid(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    BodyId: int,
    AnchorGuid: str,
) -> None:
    Cursor = SelectCursor(BulkData, Owners, BodyId, KBodyGuid)
    if Cursor.DataValue[:2] == b"\x00\x01":
        _ = ReadGeomAttrs(Cursor)
    elif Cursor.TakeBytes(2) != bytes(2):
        raise ValueError("Unsupported Fusion historical BODY prefix")
    if not Cursor.ReadText(True).startswith("0_"):
        raise ValueError("Unsupported Fusion historical BODY tag")
    Cursor.Offset += 239
    if (
        Cursor.TakeBytes(14) != b"\x00\x00\x80\x3f" + bytes(10)
        or ReadSelectUuid(Cursor) != AnchorGuid
        or Cursor.TakeBytes(11) != b"\x01\x01" + bytes(9)
    ):
        raise ValueError("Fusion historical BODY and anchor identity disagree")
