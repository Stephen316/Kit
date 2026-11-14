from struct import pack as PackFields

from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgAppInfo import DwgAppInfo
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgSummary import DwgSummary


def EmitWide(TextValue: str) -> bytes:
    Encoded = (TextValue + "\x00").encode("utf-16-le")
    return PackFields("<H", len(Encoded) // 2) + Encoded


def EmitSummary(Summary: DwgSummary) -> bytes:
    TextValues = (
        Summary.Title,
        Summary.Subject,
        Summary.Author,
        Summary.Keywords,
        Summary.Comments,
        Summary.LastSavedBy,
        Summary.RevisionNumber,
        Summary.HyperlinkBase,
    )
    Output = b"".join(EmitWide(TextValue) for TextValue in TextValues)
    Output += PackFields(
        "<6I",
        Summary.EditingTime.DayNumber,
        Summary.EditingTime.MilliSeconds,
        Summary.CreatedTime.DayNumber,
        Summary.CreatedTime.MilliSeconds,
        Summary.ModifiedTime.DayNumber,
        Summary.ModifiedTime.MilliSeconds,
    )
    Output += PackFields("<H", len(Summary.CustomProps))
    for CustomProp in Summary.CustomProps:
        Output += EmitWide(CustomProp.PropName) + EmitWide(CustomProp.PropValue)
    return Output + PackFields("<2I", *Summary.ReservedWords)


def EmitAppInfo(AppInfo: DwgAppInfo) -> bytes:
    Output = PackFields("<I", AppInfo.LeadWord) + EmitWide(AppInfo.InfoName)
    Output += PackFields("<I", len(AppInfo.AppEntries))
    for AppEntry in AppInfo.AppEntries:
        Output += AppEntry.KeyBytes + EmitWide(AppEntry.TextValue)
    return Output
