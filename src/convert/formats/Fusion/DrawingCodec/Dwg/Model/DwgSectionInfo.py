from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgPageRef import DwgPageRef


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
