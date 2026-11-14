from convert.formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.formats.Fusion.DrawingCodec.Dwg.Metadata.ReadCustomProps import (
    ReadCustomProps,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Metadata.ReadTextRun import ReadTextRun
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgDayTime import DwgDayTime
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSummary import DwgSummary


def ReadSummary(DataValue: bytes) -> DwgSummary:
    TextValues, Offset = ReadTextRun(DataValue, 0, 8)
    Clock = ReadFields(DataValue, Offset, "<6I", "summary info times")
    CustomProps, Offset = ReadCustomProps(DataValue, Offset + 24)
    ReservedWords = ReadFields(DataValue, Offset, "<2I", "summary info trailer")
    if Offset + 8 != len(DataValue):
        raise ValueError("DWG summary info has unexpected trailing bytes")
    return DwgSummary(
        Title=TextValues[0],
        Subject=TextValues[1],
        Author=TextValues[2],
        Keywords=TextValues[3],
        Comments=TextValues[4],
        LastSavedBy=TextValues[5],
        RevisionNumber=TextValues[6],
        HyperlinkBase=TextValues[7],
        EditingTime=DwgDayTime(Clock[0], Clock[1]),
        CreatedTime=DwgDayTime(Clock[2], Clock[3]),
        ModifiedTime=DwgDayTime(Clock[4], Clock[5]),
        CustomProps=CustomProps,
        ReservedWords=ReservedWords,
    )
