from convert.formats.Fusion.DrawingCodec.Author.Defaults.AutomationParts import (
    KAutomationParts,
    KDimensionGroups,
    KSettingOrder,
)
from convert.formats.Fusion.DrawingCodec.Author.Defaults.DrawingPolicy import (
    KDimensionStrategy,
)
from convert.formats.Fusion.DrawingCodec.Author.Defaults.PartColumns import (
    KPartColumns,
)
from convert.formats.Fusion.DrawingCodec.Author.Members.ColumnIdent import ColumnIdent
from convert.formats.Fusion.DrawingCodec.Author.Members.SettingTools import (
    SettingItem,
    SettingVersion,
)
from convert.formats.Fusion.DrawingCodec.Members.JsonFields import (
    JsonFields,
    KFrozenJson,
)
from convert.formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle
from convert.formats.Fusion.DrawingCodec.Members.WriteJson import WriteJson
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import KSettingsFolder


def BuildSettings(AutoDimension: bool) -> tuple[JsonPart, ...]:
    Parts = {PartValue.Name: PartValue for PartValue in KAutomationParts}
    for PartValue in (DimensionPart(AutoDimension), PartsListPart()):
        Parts[PartValue.Name] = PartValue
    return tuple(
        Parts[KSettingsFolder + StemName + ".json"] for StemName in KSettingOrder
    )


def DimensionPart(AutoDimension: bool) -> JsonPart:
    Groups: list[KFrozenJson] = []
    for GroupName, HasStrategy in KDimensionGroups:
        Items: list[KFrozenJson] = []
        if not AutoDimension:
            Items.append(SettingItem("AutoDimension", False))
        if HasStrategy:
            Items.append(SettingItem("DimensionStrategy", KDimensionStrategy))
        if Items:
            Groups.append(SettingItem(GroupName, (*Items, SettingVersion(1))))
    return JsonPart(
        KSettingsFolder + "Dimensions.json",
        (*Groups, SettingVersion(2)),
        JsonStyle.KSpaced,
    )


def PartsListPart() -> JsonPart:
    ColumnRows = tuple(
        JsonFields(
            (
                ("id", ColumnIdent(Column)),
                ("displayName", Column.DisplayName),
                ("visibility", Column.Visible),
                ("widthIso", Column.WidthIso),
                ("widthAsme", Column.WidthAsme),
                ("propOrder", Index + 1),
            )
        )
        for Index, Column in enumerate(KPartColumns)
    )
    TextValue = WriteJson(JsonFields((("properties", ColumnRows),)), JsonStyle.KCompact)
    return JsonPart(
        KSettingsFolder + "PartsListDefaultSettings.json",
        (
            SettingItem("DynamicProperties", TextValue.decode("utf-8")),
            SettingVersion(2),
        ),
        JsonStyle.KSpaced,
    )
