from struct import unpack as UnpackValue

from convert.formats.Fusion.BrepCodec.Journal.Validation.CheckModelHead import (
    CheckModelHead,
)
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import (
    KAsmWidths,
    KIntCodes,
    ReadAsmToken,
)


def ReadModelHead(
    Cursor: MetaCursor, HasHistory: bool
) -> tuple[BrepHeader, GeometryStamp]:
    Width = KAsmWidths.get(Cursor.TakeBytes(15))
    if Width is None:
        raise ValueError("Unsupported Fusion geometry signature")
    Version, Stored, Roots, Flags = UnpackValue(
        "<4" + KIntCodes[Width][1], Cursor.TakeBytes(4 * Width)
    )
    if Stored != 0:
        raise ValueError("Unsupported Fusion stored entity-count header")
    Strings: list[str] = []
    Numbers: list[float] = []
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor, Width)
        if TagValue != 7 or not isinstance(Value, str):
            raise ValueError("Invalid Fusion geometry provenance")
        Strings.append(Value)
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor, Width)
        if TagValue != 6 or not isinstance(Value, float):
            raise ValueError("Invalid Fusion geometry header scalar")
        Numbers.append(Value)
    Header = BrepHeader(
        Version, Roots, Flags, Numbers[0], Numbers[1], Numbers[2], Width
    )
    CheckModelHead(Header, HasHistory)
    return Header, GeometryStamp(*Strings)
