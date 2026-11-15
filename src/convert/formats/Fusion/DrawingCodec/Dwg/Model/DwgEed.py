from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord


# drawing eed needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgEed:
    AppRef: DwgHandleRef
    EedItems: DwgRecord
    RawData: bytes
