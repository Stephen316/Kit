from convert.formats.Fusion.DrawingCodec.Dwg.Inflate.InflatePage import InflatePage
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSectionInfo import (
    DwgSectionInfo,
)


def UnpackPage(Packed: bytes, SectionInfo: DwgSectionInfo, Needed: int) -> bytes:
    if SectionInfo.CompressFlag == 1:
        Payload = Packed
    else:
        Payload = InflatePage(Packed, SectionInfo.MaxPageSize)
    if len(Payload) < Needed:
        raise ValueError(
            f"DWG section {SectionInfo.SectionName!r} page is shorter than its declared data"
        )
    return Payload[:Needed]
