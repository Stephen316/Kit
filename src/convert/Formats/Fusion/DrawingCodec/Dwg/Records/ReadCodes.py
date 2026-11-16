from collections.abc import Callable

from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.BitCursor import BitCursor
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitLongMut import ReadBitLongMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadBitShortMut import (
    ReadBitShortMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadCodeMut import (
    ReadBitDblMut,
    ReadBitLLMut,
    ReadHandleMut,
    ReadRawDblMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawCharMut import ReadRawCharMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawLongMut import ReadRawLongMut
from convert.Formats.Fusion.DrawingCodec.Dwg.Bits.ReadRawShortMut import (
    ReadRawShortMut,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import KDwgValue
from convert.Formats.Fusion.DrawingCodec.Dwg.Records.ReadShapes import (
    ReadBitXyMut,
    ReadBitXyzMut,
    ReadExtrudeMut,
    ReadOneBitMut,
    ReadRawXyMut,
    ReadRawXyzMut,
    ReadThickMut,
    ReadTwoBitsMut,
)

# the read codes vocabulary must stay centralized so native drawing reconstruction agrees on supported native identities
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
