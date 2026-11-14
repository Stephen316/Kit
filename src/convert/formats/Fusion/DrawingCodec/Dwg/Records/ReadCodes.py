from collections.abc import Callable

from convert.formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitLongMut import ReadBitLongMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitShortMut import (
    ReadBitShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import (
    ReadBitDblMut,
    ReadBitLLMut,
    ReadHandleMut,
    ReadRawDblMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawCharMut import ReadRawCharMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawLongMut import ReadRawLongMut
from convert.formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import KDwgValue
from convert.formats.Fusion.DrawingCodec.Dwg.Records.ReadShapes import (
    ReadBitXyMut,
    ReadBitXyzMut,
    ReadExtrudeMut,
    ReadOneBitMut,
    ReadRawXyMut,
    ReadRawXyzMut,
    ReadThickMut,
    ReadTwoBitsMut,
)

KReadCodes: dict[str, Callable[[BitCursor], KDwgValue]] = {
    "B": ReadOneBitMut,
    "BB": ReadTwoBitsMut,
    "BS": ReadBitShortMut,
    "BL": ReadBitLongMut,
    "BLL": ReadBitLLMut,
    "BD": ReadBitDblMut,
    "RC": ReadRawCharMut,
    "RS": ReadRawShortMut,
    "RL": ReadRawLongMut,
    "RD": ReadRawDblMut,
    "2RD": ReadRawXyMut,
    "3RD": ReadRawXyzMut,
    "2BD": ReadBitXyMut,
    "3BD": ReadBitXyzMut,
    "BE": ReadExtrudeMut,
    "BT": ReadThickMut,
    "DH": ReadHandleMut,
}
