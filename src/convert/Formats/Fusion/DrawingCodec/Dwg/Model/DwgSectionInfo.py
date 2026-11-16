from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgPageRef import DwgPageRef


# drawing section info needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgSectionInfo:
    SectionName: str
    SectionId: int
    DataSize: int
    PageCount: int
    MaxPageSize: int
    ReservedWord: int
    CompressFlag: int
    EncryptFlag: int
    PageRefs: tuple[DwgPageRef, ...]
