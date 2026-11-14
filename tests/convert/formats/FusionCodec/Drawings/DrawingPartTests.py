from typing import cast as CastValue

from pytest import raises as ExpectError

from convert.formats.Fusion.DrawingCodec.Members.JsonFields import JsonFields
from convert.formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle
from convert.formats.Fusion.DrawingCodec.Members.PropertyCodec import (
    EmitProperties,
    ReadProperties,
)
from convert.formats.Fusion.DrawingCodec.Members.ReadJsonPart import ReadJsonPart
from convert.formats.Fusion.DrawingCodec.Members.RedirectCodec import (
    EmitRedirects,
    ReadRedirects,
)
from convert.formats.Fusion.DrawingCodec.Members.Redirections import (
    RedirectDesign,
    RedirectLink,
    Redirections,
    RedirectValue,
)
from convert.formats.Fusion.DrawingCodec.Members.SheetCodec import EmitSheet, ReadSheet
from convert.formats.Fusion.DrawingCodec.Members.SheetLayout import SheetLayout
from convert.formats.Fusion.DrawingCodec.Members.WriteJson import WriteJson

KSheetText = (
    b'{"verticalZones":"4","sheetHeight":"297.000000","sheetSize":"A3",'
    b'"units":"mm","horizontalZones":"8","sheetWidth":"420.000000",'
    b'"activeSheetName":"Sheet1","standard":"ISO"}'
)


def TestSheetLayout() -> None:
    Value = ReadSheet(KSheetText)
    assert Value == SheetLayout("Sheet1", "A3", "ISO", "mm", 420.0, 297.0, 8, 4)
    assert EmitSheet(Value) == KSheetText
    Reordered = KSheetText.replace(b'"verticalZones":"4",', b"").replace(
        b'"standard":"ISO"', b'"standard":"ISO","verticalZones":"4"'
    )
    with ExpectError(ValueError, match="fields"):
        _ = ReadSheet(Reordered)
    with ExpectError(ValueError, match="not canonical"):
        _ = ReadSheet(KSheetText.replace(b"420.000000", b"420.0"))
    with ExpectError(ValueError, match="zone count"):
        _ = EmitSheet(SheetLayout("Sheet1", "A3", "ISO", "mm", 420.0, 297.0, 0, 4))
    with ExpectError(ValueError, match="extent"):
        _ = EmitSheet(SheetLayout("Sheet1", "A3", "ISO", "mm", 420, 297.0, 8, 4))


def TestJsonStyles() -> None:
    Spaced = b'{"enabled" : true,"rows" : [1,2.5,"x"],"nested" : {"k" : null}}'
    PartValue = ReadJsonPart("AutomationSettings/Dimensions.json", Spaced)
    assert PartValue.Style is JsonStyle.KSpaced
    assert WriteJson(PartValue.Value, PartValue.Style) == Spaced
    Compact = WriteJson(PartValue.Value, JsonStyle.KCompact)
    assert Compact == b'{"enabled":true,"rows":[1,2.5,"x"],"nested":{"k":null}}'
    assert ReadJsonPart("ComponentReferenceData.json", Compact) == JsonPart(
        "ComponentReferenceData.json", PartValue.Value, JsonStyle.KCompact
    )
    with ExpectError(ValueError, match="formatting"):
        _ = ReadJsonPart("Pretty.json", b'{\n  "enabled": true\n}')
    Duplicate = JsonFields((("k", 1), ("k", 2)))
    with ExpectError(ValueError, match="duplicate"):
        _ = WriteJson(Duplicate, JsonStyle.KCompact)


def TestProperties() -> None:
    Empty = JsonFields(())
    assert EmitProperties(Empty) == b"\x02\x00\x00\x00{}"
    assert ReadProperties(b"\x02\x00\x00\x00{}") == Empty
    with ExpectError(ValueError, match="length"):
        _ = ReadProperties(b"\x03\x00\x00\x00{}")
    with ExpectError(ValueError, match="JSON object"):
        _ = EmitProperties(CastValue(JsonFields, ()))


def TestRedirects() -> None:
    Value = Redirections(
        1,
        (RedirectDesign(2, "Boxes.f3d", "Boxes", "urn:lineage:A", "urn:version:A"),),
        (
            RedirectLink(
                "Drawing.f2d",
                "Boxes.f3d",
                "xref",
                (RedirectValue("linkedAssetGUID", "guid", "string"),),
            ),
        ),
    )
    Payload = EmitRedirects(Value)
    assert Payload.startswith(b'{"name":"RedirectionsStream","schema-version":1,')
    assert ReadRedirects(Payload) == Value
    with ExpectError(ValueError, match="not canonical"):
        _ = ReadRedirects(Payload.replace(b",", b", ", 1))
