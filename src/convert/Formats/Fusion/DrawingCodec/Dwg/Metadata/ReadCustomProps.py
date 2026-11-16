from convert.Formats.Fusion.DrawingCodec.Dwg.Bytes.ReadFields import ReadFields
from convert.Formats.Fusion.DrawingCodec.Dwg.Metadata.ReadTextRun import ReadTextRun
from convert.Formats.Fusion.DrawingCodec.Dwg.Model.DwgCustomProp import DwgCustomProp


# the custom props operation needs a distinct decoding boundary so section boundaries and object references remain consistent
def ReadCustomProps(
    DataValue: bytes, Offset: int
) -> tuple[tuple[DwgCustomProp, ...], int]:
    Count = ReadFields(DataValue, Offset, "<H", "custom property count")[0]
    TextValues, Position = ReadTextRun(DataValue, Offset + 2, Count * 2)
    CustomProps = tuple(
        DwgCustomProp(PropName, PropValue)
        for PropName, PropValue in zip(TextValues[0::2], TextValues[1::2], strict=True)
    )
    return CustomProps, Position
