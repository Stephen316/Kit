from convert.formats.Fusion.DrawingCodec.Dwg.Header.EmitHeaderVars import (
    EmitHeaderVars,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Header.HeaderFrame import KHeaderName
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgFileHeader import DwgFileHeader
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgRecord import DwgRecord
from convert.formats.Fusion.DrawingCodec.Dwg.Sections.SectionCodecs import (
    EmitSection,
)


def EncodeSections(
    HeaderVars: DwgRecord,
    SectionVars: tuple[tuple[str, DwgRecord], ...],
    FileHeader: DwgFileHeader,
) -> dict[str, bytes]:
    Contents: dict[str, bytes] = {}
    Frames = dict(SectionVars)
    if HeaderVars.RecordFields:
        Frame = Frames.get(KHeaderName, DwgRecord(()))
        Contents[KHeaderName] = EmitHeaderVars(HeaderVars, Frame, FileHeader)
    for SectionName, Record in SectionVars:
        if SectionName != KHeaderName:
            VersionText = FileHeader.VersionText
            Contents[SectionName] = EmitSection(SectionName, Record, VersionText)
    return Contents
