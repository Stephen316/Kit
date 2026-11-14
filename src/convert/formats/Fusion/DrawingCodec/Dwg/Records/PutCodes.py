from collections.abc import Callable

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitWriter import BitWriter
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import KDwgValue
from convert.formats.Fusion.DrawingCodec.Dwg.Records.PutShapes import (
    PutBdValueMut,
    PutBitXyMut,
    PutBitXyzMut,
    PutBllValueMut,
    PutBlValueMut,
    PutBsValueMut,
    PutDataRefMut,
    PutExtrudeMut,
    PutOneBitMut,
    PutRawXyMut,
    PutRawXyzMut,
    PutRcValueMut,
    PutRdValueMut,
    PutRlValueMut,
    PutRsValueMut,
    PutThickMut,
    PutTwoBitsMut,
)

KPutCodes: dict[str, Callable[[BitWriter, KDwgValue], None]] = {
    "B": PutOneBitMut,
    "BB": PutTwoBitsMut,
    "BS": PutBsValueMut,
    "BL": PutBlValueMut,
    "BLL": PutBllValueMut,
    "BD": PutBdValueMut,
    "RC": PutRcValueMut,
    "RS": PutRsValueMut,
    "RL": PutRlValueMut,
    "RD": PutRdValueMut,
    "2RD": PutRawXyMut,
    "3RD": PutRawXyzMut,
    "2BD": PutBitXyMut,
    "3BD": PutBitXyzMut,
    "BE": PutExtrudeMut,
    "BT": PutThickMut,
    "DH": PutDataRefMut,
}
