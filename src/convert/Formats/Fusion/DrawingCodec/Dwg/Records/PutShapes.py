from struct import pack as PackFields

from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.PutCodeMut import (
    PutBitDblMut,
    PutBitLLMut,
    PutBitLongMut,
    PutBitShortMut,
    PutHandleMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.PutRawMut import (
    PutRawCharMut,
    PutRawDblMut,
    PutRawLongMut,
    PutRawShortMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import KDwgValue
from convert.Formats.Fusion.DrawingCodec.Dwg.Records.CoerceValue import (
    AsFloat,
    AsHandle,
    AsInt,
    AsPoint,
)

# unit z must remain consistent across callers so section boundaries and object references remain consistent
KUnitZ = PackFields("<3d", 0.0, 0.0, 1.0)

# zero bits must remain consistent across callers so section boundaries and object references remain consistent
KZeroBits = PackFields("<d", 0.0)


# the one bit operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutOneBitMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Writer.PutBits(AsInt(Value), 1)


# the two bits operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutTwoBitsMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Writer.PutBits(AsInt(Value), 2)


# the bs value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutBsValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitShortMut(Writer, AsInt(Value))


# the bl value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutBlValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitLongMut(Writer, AsInt(Value))


# the bll value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutBllValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitLLMut(Writer, AsInt(Value))


# the bd value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutBdValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutBitDblMut(Writer, AsFloat(Value))


# the rc value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutRcValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawCharMut(Writer, AsInt(Value))


# the rs value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutRsValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawShortMut(Writer, AsInt(Value))


# the rl value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutRlValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawLongMut(Writer, AsInt(Value))


# the rd value operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutRdValueMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutRawDblMut(Writer, AsFloat(Value))


# the raw xy operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutRawXyMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 2):
        PutRawDblMut(Writer, Coordinate)


# the raw xyz operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutRawXyzMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 3):
        PutRawDblMut(Writer, Coordinate)


# the bit xy operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutBitXyMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 2):
        PutBitDblMut(Writer, Coordinate)


# the bit xyz operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutBitXyzMut(Writer: BitWriter, Value: KDwgValue) -> None:
    for Coordinate in AsPoint(Value, 3):
        PutBitDblMut(Writer, Coordinate)


# the extrude operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutExtrudeMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Points = AsPoint(Value, 3)
    IsUnit = PackFields("<3d", *Points) == KUnitZ
    Writer.PutBits(1 if IsUnit else 0, 1)
    if not IsUnit:
        PutBitXyzMut(Writer, Points)


# the thick operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutThickMut(Writer: BitWriter, Value: KDwgValue) -> None:
    Thickness = AsFloat(Value)
    IsZero = PackFields("<d", Thickness) == KZeroBits
    Writer.PutBits(1 if IsZero else 0, 1)
    if not IsZero:
        PutBitDblMut(Writer, Thickness)


# the data reference operation needs a consistent construction rule so section boundaries and object references remain consistent
def PutDataRefMut(Writer: BitWriter, Value: KDwgValue) -> None:
    PutHandleMut(Writer, AsHandle(Value))
