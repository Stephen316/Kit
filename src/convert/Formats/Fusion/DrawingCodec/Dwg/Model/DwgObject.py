from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgEed import DwgEed
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord


# drawing object needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgObject:
    TypeNumber: int
    ObjectHandle: int
    EedBlocks: tuple[DwgEed, ...]
    CommonKind: str
    CommonData: DwgRecord
    ClassKind: str
    ClassData: DwgRecord
    TailWidth: int
    TailValue: int
    TextItems: tuple[str, ...]
    HasTexts: bool
    HandleRefs: tuple[DwgHandleRef, ...]
