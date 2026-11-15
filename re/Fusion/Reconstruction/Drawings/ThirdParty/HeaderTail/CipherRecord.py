from functools import lru_cache
from struct import pack as PackFields
from struct import unpack as UnpackFields

KWordCount = 18 + 4 * 256
KProductKey = bytes.fromhex("e1a43cf0aa69e0e31755c78100d809de")
KMask = 0xFFFFFFFF


def ArcTanInverse(InverseValue: int, UnitValue: int) -> int:
    Total = 0
    TermValue = UnitValue // InverseValue
    Square = InverseValue * InverseValue
    Index = 1
    SignValue = 1
    while TermValue:
        Total += SignValue * (TermValue // Index)
        TermValue //= Square
        Index += 2
        SignValue = -SignValue
    return Total


def PiWords(WordCount: int) -> tuple[int, ...]:
    HexCount = WordCount * 8
    DigitCount = HexCount * 2 + 80
    UnitValue = 10**DigitCount
    PiValue = 16 * ArcTanInverse(5, UnitValue) - 4 * ArcTanInverse(239, UnitValue)
    Scaled = (PiValue - 3 * UnitValue) * 16**HexCount // UnitValue
    TextValue = format(Scaled, "0%dx" % HexCount)
    return tuple(
        int(TextValue[Start : Start + 8], 16) for Start in range(0, HexCount, 8)
    )


def KeySchedule(
    KeyValue: bytes,
) -> tuple[list[int], list[int], list[int], list[int], list[int]]:
    Words = PiWords(KWordCount)
    PValue = list(Words[:18])
    BoxAValue = list(Words[18 : 18 + 256])
    BoxBValue = list(Words[18 + 256 : 18 + 512])
    BoxCValue = list(Words[18 + 512 : 18 + 768])
    BoxDValue = list(Words[18 + 768 : 18 + 1024])
    KeyIndex = 0
    for Index in range(18):
        KeyWord = 0
        for _ in range(4):
            KeyWord = ((KeyWord << 8) | KeyValue[KeyIndex]) & KMask
            KeyIndex = (KeyIndex + 1) % len(KeyValue)
        PValue[Index] ^= KeyWord
    LeftValue = 0
    RightValue = 0
    for Index in range(0, 18, 2):
        LeftValue, RightValue = EncryptBlock(
            LeftValue, RightValue, PValue, BoxAValue, BoxBValue, BoxCValue, BoxDValue
        )
        PValue[Index], PValue[Index + 1] = LeftValue, RightValue
    for BoxValue in (BoxAValue, BoxBValue, BoxCValue, BoxDValue):
        for Index in range(0, 256, 2):
            LeftValue, RightValue = EncryptBlock(
                LeftValue,
                RightValue,
                PValue,
                BoxAValue,
                BoxBValue,
                BoxCValue,
                BoxDValue,
            )
            BoxValue[Index], BoxValue[Index + 1] = LeftValue, RightValue
    return PValue, BoxAValue, BoxBValue, BoxCValue, BoxDValue


def FuncValue(
    Value: int,
    BoxAValue: list[int],
    BoxBValue: list[int],
    BoxCValue: list[int],
    BoxDValue: list[int],
) -> int:
    AValue = (Value >> 24) & 0xFF
    BValue = (Value >> 16) & 0xFF
    CValue = (Value >> 8) & 0xFF
    DValue = Value & 0xFF
    Result = (BoxAValue[AValue] + BoxBValue[BValue]) & KMask
    Result ^= BoxCValue[CValue]
    return (Result + BoxDValue[DValue]) & KMask


def EncryptBlock(
    LeftValue: int,
    RightValue: int,
    PValue: list[int],
    BoxAValue: list[int],
    BoxBValue: list[int],
    BoxCValue: list[int],
    BoxDValue: list[int],
) -> tuple[int, int]:
    for Index in range(16):
        LeftValue ^= PValue[Index]
        RightValue ^= FuncValue(LeftValue, BoxAValue, BoxBValue, BoxCValue, BoxDValue)
        LeftValue, RightValue = RightValue, LeftValue
    LeftValue, RightValue = RightValue, LeftValue
    RightValue ^= PValue[16]
    LeftValue ^= PValue[17]
    return LeftValue & KMask, RightValue & KMask


def DecryptBlock(
    LeftValue: int,
    RightValue: int,
    PValue: list[int],
    BoxAValue: list[int],
    BoxBValue: list[int],
    BoxCValue: list[int],
    BoxDValue: list[int],
) -> tuple[int, int]:
    for Index in range(17, 1, -1):
        LeftValue ^= PValue[Index]
        RightValue ^= FuncValue(LeftValue, BoxAValue, BoxBValue, BoxCValue, BoxDValue)
        LeftValue, RightValue = RightValue, LeftValue
    LeftValue, RightValue = RightValue, LeftValue
    RightValue ^= PValue[1]
    LeftValue ^= PValue[0]
    return LeftValue & KMask, RightValue & KMask


@lru_cache(maxsize=1)
def KState() -> tuple[list[int], list[int], list[int], list[int], list[int]]:
    return KeySchedule(KProductKey)


def EncryptBytes(DataValue: bytes) -> bytes:
    LeftValue, RightValue = UnpackFields(">II", DataValue)
    LeftValue, RightValue = EncryptBlock(LeftValue, RightValue, *KState())
    return PackFields(">II", LeftValue, RightValue)


def DecryptBytes(DataValue: bytes) -> bytes:
    LeftValue, RightValue = UnpackFields(">II", DataValue)
    LeftValue, RightValue = DecryptBlock(LeftValue, RightValue, *KState())
    return PackFields(">II", LeftValue, RightValue)
