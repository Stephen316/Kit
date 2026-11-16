from dataclasses import dataclass as MakeDataClass

from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgClassTable import DwgClassTable
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgCryptHeader import (
    DwgCryptHeader,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgObject import DwgObject
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgPageImage import DwgPageImage
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgSummary import DwgSummary


# drawing file needs an explicit state contract so section boundaries and object references remain consistent
@MakeDataClass(frozen=True, slots=True)
class DwgFile:
    FileHeader: DwgFileHeader
    CryptHeader: DwgCryptHeader
    MapWords: tuple[int, ...]
    SectionInfos: tuple[DwgSectionInfo, ...]
    NameFields: tuple[bytes, ...]
    PageImages: tuple[DwgPageImage, ...]
    HeaderVars: DwgRecord
    ClassTable: DwgClassTable
    DwgObjects: tuple[DwgObject, ...]
    Summary: DwgSummary | None
    AppInfo: DwgAppInfo | None
    SectionVars: tuple[tuple[str, DwgRecord], ...]
    RawSections: tuple[tuple[str, bytes], ...]
    HeaderBytes: bytes = b""
