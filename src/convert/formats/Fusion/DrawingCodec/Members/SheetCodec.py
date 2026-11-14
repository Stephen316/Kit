from math import isfinite as IsFinite
from typing import cast as CastValue

from convert.formats.Fusion.BundleCodec.Json.EmitJson import EmitJson
from convert.formats.Fusion.BundleCodec.Json.JsonTypes import KJsonValue
from convert.formats.Fusion.BundleCodec.Json.ReadJson import ReadJson
from convert.formats.Fusion.DrawingCodec.Members.SheetLayout import SheetLayout

KSheetKeys = (
    "verticalZones",
    "sheetHeight",
    "sheetSize",
    "units",
    "horizontalZones",
    "sheetWidth",
    "activeSheetName",
    "standard",
)


def EmitSheet(Value: SheetLayout) -> bytes:
    if not isinstance(CastValue(object, Value), SheetLayout):
        raise ValueError("Expected a typed Fusion drawing sheet layout")
    Numbers = (Value.Width, Value.Height)
    Zones = (Value.HorizontalZones, Value.VerticalZones)
    if any(type(Number) is not float or not IsFinite(Number) for Number in Numbers):
        raise ValueError("Invalid Fusion drawing sheet extent")
    if any(type(Count) is not int or not 0 < Count < 1000 for Count in Zones):
        raise ValueError("Invalid Fusion drawing sheet zone count")
    Texts = (Value.ActiveSheet, Value.SheetSize, Value.Units, Value.Standard)
    if any(
        type(TextValue) is not str or not TextValue.isascii() for TextValue in Texts
    ):
        raise ValueError("Unsupported Fusion drawing sheet text")
    Fields: dict[str, KJsonValue] = {
        "verticalZones": str(Value.VerticalZones),
        "sheetHeight": f"{Value.Height:.6f}",
        "sheetSize": Value.SheetSize,
        "units": Value.Units,
        "horizontalZones": str(Value.HorizontalZones),
        "sheetWidth": f"{Value.Width:.6f}",
        "activeSheetName": Value.ActiveSheet,
        "standard": Value.Standard,
    }
    return EmitJson(Fields)


def ReadSheet(Payload: bytes) -> SheetLayout:
    Fields = ReadJson(Payload)
    if not isinstance(Fields, dict) or tuple(Fields) != KSheetKeys:
        raise ValueError("Unsupported Fusion drawing sheet manifest fields")
    if any(type(ItemValue) is not str for ItemValue in Fields.values()):
        raise ValueError("Unsupported Fusion drawing sheet manifest values")
    Texts = CastValue(dict[str, str], Fields)
    try:
        Result = SheetLayout(
            Texts["activeSheetName"],
            Texts["sheetSize"],
            Texts["standard"],
            Texts["units"],
            float(Texts["sheetWidth"]),
            float(Texts["sheetHeight"]),
            int(Texts["horizontalZones"]),
            int(Texts["verticalZones"]),
        )
    except ValueError as ErrorInfo:
        raise ValueError("Invalid Fusion drawing sheet manifest number") from ErrorInfo
    if EmitSheet(Result) != Payload:
        raise ValueError("Fusion drawing sheet manifest is not canonical")
    return Result
