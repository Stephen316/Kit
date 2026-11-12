from dataclasses import dataclass as MakeDataClass
from math import isfinite as IsFinite
from struct import unpack as Unpack
from typing import TypeAlias

from convert.formats.Fusion.MetaCursor import MetaCursor

# typed framing retains unknown scalar tokens outside the selected source body
KAsmValue: TypeAlias = int | float | str | bytes | tuple[float, ...] | None

# each serialized token keeps the wire discriminator needed by field readers
KAsmToken: TypeAlias = tuple[int, KAsmValue]


# initial entity ordinals are separate from stored body handles and history slots
@MakeDataClass(frozen=True, slots=True)
class AsmRecord:
    Name: str
    Tokens: tuple[KAsmToken, ...]


# declared initial roots never include trailing journal states
@MakeDataClass(frozen=True, slots=True)
class AsmTable:
    RootCount: int
    Records: tuple[AsmRecord, ...]


# a focused initial reader consumes every token by its bounded wire grammar
def ReadAsmToken(Cursor: MetaCursor) -> KAsmToken:
    TagValue = Cursor.TakeBytes(1)[0]
    if TagValue in (4, 12, 21, 23):
        Value = Unpack("<q", Cursor.TakeBytes(8))[0]
    elif TagValue == 6:
        Value = Unpack("<d", Cursor.TakeBytes(8))[0]
        if not IsFinite(Value):
            raise ValueError("Nonfinite Fusion ASM scalar")
    elif TagValue in (7, 13, 14):
        Value = Cursor.TakeBytes(Cursor.TakeBytes(1)[0]).decode("ascii")
    elif TagValue == 18:
        SizeValue = Unpack("<q", Cursor.TakeBytes(8))[0]
        Value = Cursor.TakeBytes(SizeValue)
    elif TagValue in (19, 20):
        Value = Unpack("<3d", Cursor.TakeBytes(24))
        if not all(map(IsFinite, Value)):
            raise ValueError("Nonfinite Fusion ASM vector")
    elif TagValue in (10, 11, 15, 16, 17):
        Value = None
    else:
        raise ValueError("Unsupported Fusion ASM token")
    return TagValue, Value


# recursive entity subtype delimiters are framed but not evaluated
def ReadAsmRecord(Cursor: MetaCursor, NameValue: str) -> AsmRecord:
    Tokens: list[KAsmToken] = []
    Depth = 0
    for _ in range(4096):
        Token = ReadAsmToken(Cursor)
        TagValue = Token[0]
        if TagValue == 17:
            if Depth:
                raise ValueError("Unbalanced Fusion ASM record")
            return AsmRecord(NameValue, tuple(Tokens))
        if TagValue in (15, 16):
            Depth += 1 if TagValue == 15 else -1
            if not 0 <= Depth <= 32:
                raise ValueError("Unbalanced Fusion ASM subtype")
        Tokens.append(Token)
    raise ValueError("Oversized Fusion ASM record")


# entity names can have one or more typed class prefixes
def ReadAsmName(Cursor: MetaCursor) -> str:
    Parts: list[str] = []
    for _ in range(8):
        TagValue, TextValue = ReadAsmToken(Cursor)
        if (
            TagValue not in (13, 14)
            or not isinstance(TextValue, str)
            or not TextValue
            or not TextValue.isprintable()
        ):
            raise ValueError("Invalid Fusion ASM entity name")
        Parts.append(TextValue)
        if TagValue == 13:
            return "-".join(Parts)
    raise ValueError("Oversized Fusion ASM entity name")


# the history boundary isolates the only topology generation used as source evidence
def ReadAsmTable(BlobData: bytes) -> AsmTable:
    if len(BlobData) > 2 * 1024 * 1024:
        raise ValueError("Fusion ASM selection cache exceeds its size limit")
    Cursor = MetaCursor(BlobData)
    if Cursor.TakeBytes(15) != b"ASM BinaryFile8":
        raise ValueError("Unsupported Fusion ASM file header")
    Version, Stored, Roots, Flags = Unpack("<4q", Cursor.TakeBytes(32))
    if Version <= 0 or Stored != 0 or not 2 <= Roots <= 256 or Flags != 3:
        raise ValueError("Unsupported Fusion ASM history header")
    Header = tuple(ReadAsmToken(Cursor) for _ in range(6))
    if tuple(Token[0] for Token in Header) != (7, 7, 7, 6, 6, 6):
        raise ValueError("Invalid Fusion ASM header tokens")
    Records: list[AsmRecord] = []
    for _ in range(8192):
        NameValue = ReadAsmName(Cursor)
        if NameValue == "Begin-of-ASM-History-Data":
            if not Roots <= len(Records) or Records[0].Name != "asmheader":
                raise ValueError("Invalid Fusion ASM root table extent")
            return AsmTable(Roots, tuple(Records))
        Records.append(ReadAsmRecord(Cursor, NameValue))
    raise ValueError("Fusion ASM initial record table exceeds its size limit")
