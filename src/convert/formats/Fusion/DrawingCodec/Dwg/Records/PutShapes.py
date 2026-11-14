from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import (
    PutBitDblMut,
    PutBitLLMut,
    PutBitLongMut,
    PutBitShortMut,
    PutHandleMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import (
    PutRawCharMut,
    PutRawDblMut,
    PutRawLongMut,
    PutRawShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import KDwgValue
from convert.formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsFloat,
    AsHandle,
    AsInt,
    AsPoint,
)

KUnitZ = PackFields("<3d", 0.0, 0.0, 1.0)
KZeroBits = PackFields("<d", 0.0)


def PutOneBitMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Writer.PutBits(AsInt(Value), 1)


def PutTwoBitsMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Writer.PutBits(AsInt(Value), 2)


def PutBsValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitShortMut(Writer, AsInt(Value))


def PutBlValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitLongMut(Writer, AsInt(Value))


def PutBllValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitLLMut(Writer, AsInt(Value))


def PutBdValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitDblMut(Writer, AsFloat(Value))


def PutRcValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawCharMut(Writer, AsInt(Value))


def PutRsValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawShortMut(Writer, AsInt(Value))


def PutRlValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawLongMut(Writer, AsInt(Value))


def PutRdValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawDblMut(Writer, AsFloat(Value))


def PutRawXyMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 2):
        PutRawDblMut(Writer, Coordinate)


def PutRawXyzMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 3):
        PutRawDblMut(Writer, Coordinate)


def PutBitXyMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 2):
        PutBitDblMut(Writer, Coordinate)


def PutBitXyzMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 3):
        PutBitDblMut(Writer, Coordinate)


def PutExtrudeMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Points = AsPoint(Value, 3)
    IsUnit = PackFields("<3d", *Points) == KUnitZ
    Writer.PutBits(1 if IsUnit else 0, 1)
    if not IsUnit:
        PutBitXyzMut(Writer, Points)


def PutThickMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Thickness = AsFloat(Value)
    IsZero = PackFields("<d", Thickness) == KZeroBits
    Writer.PutBits(1 if IsZero else 0, 1)
    if not IsZero:
        PutBitDblMut(Writer, Thickness)


def PutDataRefMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutHandleMut(Writer, AsHandle(Value))
