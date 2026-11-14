from convert.formats.Fusion.DrawingCodec.Author.Members.SettingTools import (
    SettingItem,
    SettingVersion,
)
from convert.formats.Fusion.DrawingCodec.Members.JsonPart import JsonPart
from convert.formats.Fusion.DrawingCodec.Members.JsonStyle import JsonStyle
from convert.formats.Fusion.DrawingCodec.Model.DrawingNames import KSettingsFolder

KSettingOrder = (
    "AutomaticDrawingGeneration",
    "AssemblyViewDefaultSettings",
    "Dimensions",
    "FoldedCompViewDefaultSettings",
    "FlatPatternViewDefaultSettings",
    "AnimationViewDefaultSettings",
    "PartsListDefaultSettings",
    "ComponentViewDefaultSettings",
    "SubAssemblyViewDefaultSettings",
)

KDimensionGroups = (
    ("MainAssemblyAnnotationSettings", False),
    ("SubAssemblyAnnotationSettings", False),
    ("ComponentAnnotationSettings", True),
    ("SMFoldedAnnotationSettings", True),
    ("SMFlatPatternAnnotationSettings", True),
)

KAutomationParts = (
    JsonPart(
        KSettingsFolder + "AutomaticDrawingGeneration.json",
        (
            SettingItem(
                "MainAssemblyGroup",
                (
                    SettingItem(
                        "MainAssemblyOrthoGroup",
                        (
                            SettingItem("MainAsmOrthoPartListLoc", "DLTopLeft"),
                            SettingVersion(0),
                        ),
                    ),
                    SettingVersion(0),
                ),
            ),
            SettingItem(
                "SubAssemblyGroup",
                (
                    SettingItem("SubAsmSheetCreate", False),
                    SettingItem(
                        "SubAssemblyOrthoGroup",
                        (
                            SettingItem("SubAsmOrthoPartListLoc", "DLTopLeft"),
                            SettingVersion(0),
                        ),
                    ),
                    SettingVersion(0),
                ),
            ),
            SettingItem(
                "SheetMetalFlatGroup",
                (
                    SettingItem("SheetMetalFlatPatterIncludeBendTableLoc", "DLTopLeft"),
                    SettingVersion(0),
                ),
            ),
            SettingVersion(1),
        ),
        JsonStyle.KSpaced,
    ),
    JsonPart(
        KSettingsFolder + "AssemblyViewDefaultSettings.json",
        (SettingItem("VisibilityFlags", 17), SettingVersion(1)),
        JsonStyle.KSpaced,
    ),
    JsonPart(
        KSettingsFolder + "FoldedCompViewDefaultSettings.json",
        (SettingItem("VisibilityFlags", 17), SettingVersion(1)),
        JsonStyle.KSpaced,
    ),
    JsonPart(
        KSettingsFolder + "FlatPatternViewDefaultSettings.json",
        (SettingItem("VisibilityFlags", 12), SettingVersion(1)),
        JsonStyle.KSpaced,
    ),
    JsonPart(
        KSettingsFolder + "AnimationViewDefaultSettings.json",
        (
            SettingItem("Style", 1),
            SettingItem("VisibilityFlags", 17),
            SettingVersion(1),
        ),
        JsonStyle.KSpaced,
    ),
    JsonPart(
        KSettingsFolder + "ComponentViewDefaultSettings.json",
        (SettingItem("Style", 1), SettingVersion(1)),
        JsonStyle.KSpaced,
    ),
    JsonPart(
        KSettingsFolder + "SubAssemblyViewDefaultSettings.json",
        (SettingItem("VisibilityFlags", 17), SettingVersion(1)),
        JsonStyle.KSpaced,
    ),
)
