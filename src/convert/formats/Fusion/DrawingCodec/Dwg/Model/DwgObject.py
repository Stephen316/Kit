from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgEed import DwgEed
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgHandleRef import DwgHandleRef
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord


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
