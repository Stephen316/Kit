# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the ordinary sketch and optional Boss keyword inventory."""

from collections.abc import Callable
from decimal import Decimal
from typing import cast

from HeaderLogs import KDefaultIds, KMaxTreeId
from PartFeatureIndex import KConfiguration, KDeclaration, PartIndex
from PartManifests import EncodeXml

KKeywordsXml = "swXmlContents/KeyWords"
KKeywordPrefix = bytes((0x86,))
KMaterial = "Material <not specified>"
# the exploded view and presentation reserve the two unlogged system slots
KReservedIds = frozenset((*KDefaultIds, 19, 20))
KWidth = "width_mm"
KHeight = "height_mm"
KDepth = "depth_mm"

DimensionNode = tuple[str, dict[str, str], str]
KeywordNode = tuple[str, dict[str, str], tuple[DimensionNode, ...] | None]
KeywordDrivers = tuple[tuple[str, Decimal], tuple[str, Decimal]]
KeywordBoss = tuple[str, Decimal]

# declared native feature names and types follow lexical order of their saved ids
KBuiltinEntries = (
    (1, "Annotations", "Annotations"),
    (10, "Surface Bodies", "Surface Bodies"),
    (11, KMaterial, "SOLIDWORKS Materials"),
    (12, "Ambient", "Ambient"),
    (13, "Directional1", "Directional"),
    (14, "Directional2", "Directional"),
    (15, "Directional3", "Directional"),
    (16, "Equations", "Equations"),
    (17, "Notes", "Notes"),
    (18, "Notes1___EndTag___", "Notes"),
    (19, "", "Exploded Views"),
    (2, "Front Plane", "Plane"),
    (21, "Markups", "Markups"),
    (22, "Sensors", "Sensors"),
    (23, "Favorites", "Favorites"),
    (24, "History", "History"),
    (25, "Selection Sets", "Selection Sets"),
    (3, "Top Plane", "Plane"),
    (4, "Right Plane", "Plane"),
    (6, "Lights and Cameras", "Lights and Cameras"),
    (7, "Design Binder", "Design Binder"),
    (8, "Comments", "Comments"),
    (9, "Solid Bodies", "Solid Bodies"),
)


# the index carries the saved display number in document units and can omit a sign
def DisplayDimension(Name: str, Value: Decimal) -> DimensionNode:
    if not Value.is_finite() or Value <= 0:
        raise ValueError("keyword dimension must have a positive finite display value")
    Display = format(Value, "f")
    if "." in Display:
        Display = Display.rstrip("0").rstrip(".")
    return ("Dimension", {"Name": Name}, Display)


# the Boss owns depth while the saved rectangle owns its ordered two dimensions
def EncodeKeywords(
    Part: PartIndex,
    SketchName: str,
    SketchValues: KeywordDrivers,
    Boss: KeywordBoss | None,
    *,
    SketchTreeId: int,
    BossTreeId: int | None,
) -> bytes:
    Ids = (SketchTreeId,) if BossTreeId is None else (SketchTreeId, BossTreeId)
    if (
        (Boss is None) != (BossTreeId is None)
        or SketchTreeId == BossTreeId
        or any(
            type(Id) is not int or not 0 < Id <= KMaxTreeId or Id in KReservedIds
            for Id in Ids
        )
    ):
        raise ValueError("keyword features require distinct allocated tree IDs")
    if not SketchName or {Name for Name, _ in SketchValues} != {KWidth, KHeight}:
        raise ValueError("keyword rectangle needs its named width and height")
    Configuration = (
        "Configuration",
        {
            "id": "0",
            "Name": KConfiguration,
            "Type": "ConfigurationManager",
            "Material": KMaterial,
        },
        None,
    )
    Entries: list[KeywordNode] = [Configuration]
    SketchFields = {"id": str(SketchTreeId), "Name": SketchName, "Dissectable": "true"}
    if Boss is None:
        SketchFields["DissectableRoot"] = "true"
    else:
        BossName, Depth = Boss
        if not BossName:
            raise ValueError("keyword Boss requires its own feature name")
        Entries.append(
            (
                "Extrusion",
                {"id": str(BossTreeId), "Name": BossName, "Type": "Boss-Extrude"},
                (DisplayDimension(KDepth, Depth),),
            )
        )
    Entries.extend(
        ("Feature", {"id": str(Slot), "Name": Name, "Type": Kind}, None)
        for Slot, Name, Kind in KBuiltinEntries
    )
    Entries.extend(
        (
            (
                "Sketch",
                SketchFields,
                tuple(DisplayDimension(Name, Value) for Name, Value in SketchValues),
            ),
            ("Sketch", {"id": "5", "Name": "Origin", "Type": "Origin"}, None),
        )
    )
    EncodeKeywordXml = cast(
        Callable[[str, str, dict[str, str], list[KeywordNode]], bytes], EncodeXml
    )
    return KKeywordPrefix + EncodeKeywordXml(
        KDeclaration,
        "Keywords",
        {"id": str(Part.CreatedSeconds), "Name": Part.DocumentReference},
        Entries,
    )
