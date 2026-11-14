from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.TakeSpan import TakeSpan
from convert.formats.Fusion.DrawingCodec.Dwg.Metadata.ReadWideText import ReadWideText
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppEntry import DwgAppEntry
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo


def ReadAppInfo(DataValue: bytes) -> DwgAppInfo:
    LeadWord = ReadFields(DataValue, 0, "<I", "app info lead word")[0]
    InfoName, Offset = ReadWideText(DataValue, 4)
    Count = ReadFields(DataValue, Offset, "<I", "app info entry count")[0]
    Offset += 4
    if Count > (len(DataValue) - Offset) // 18:
        raise ValueError("DWG app info entry count exceeds the section data")
    AppEntries: list[DwgAppEntry] = []
    for _ in range(Count):
        KeyBytes = TakeSpan(DataValue, Offset, 16, "app info entry key")
        TextValue, Offset = ReadWideText(DataValue, Offset + 16)
        AppEntries.append(DwgAppEntry(KeyBytes, TextValue))
    if Offset != len(DataValue):
        raise ValueError("DWG app info has unexpected trailing bytes")
    return DwgAppInfo(LeadWord, InfoName, tuple(AppEntries))
