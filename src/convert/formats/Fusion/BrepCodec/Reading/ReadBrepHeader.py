from struct import unpack as UnpackValue

from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.GeometryCodec.GeometryStamp import GeometryStamp
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmToken


def ReadBrepHeadMut(
    Cursor: MetaCursor, HasHistory: bool
) -> tuple[BrepHeader, GeometryStamp]:
    if Cursor.TakeBytes(15) != b"ASM BinaryFile8":
        raise ValueError("Unsupported Fusion BRep binary header")
    Version, Stored, Roots, Flags = UnpackValue("<4q", Cursor.TakeBytes(32))
    if (Version, Stored, Roots, Flags) != (
        23200,
        0,
        2 if HasHistory else 4,
        3 if HasHistory else 2,
    ):
        raise ValueError("Unsupported Fusion BRep header profile")
    Strings: list[str] = []
    Numbers: list[float] = []
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor)
        if TagValue != 7 or not isinstance(Value, str):
            raise ValueError("Invalid Fusion BRep provenance field")
        Strings.append(Value)
    for _ in range(3):
        TagValue, Value = ReadAsmToken(Cursor)
        if TagValue != 6 or not isinstance(Value, float):
            raise ValueError("Invalid Fusion BRep numeric header")
        Numbers.append(Value)
    if tuple(Numbers) != (50.0 if HasHistory else 10.0, 1e-6, 1e-10):
        raise ValueError("Unsupported Fusion BRep scale or tolerances")
    Header = BrepHeader(Version, Roots, Flags, Numbers[0], Numbers[1], Numbers[2])
    return Header, GeometryStamp(*Strings)
