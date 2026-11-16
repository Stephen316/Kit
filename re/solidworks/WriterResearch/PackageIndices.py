# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Bind native sidecar summaries to the generated ordinary feature state."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import PureWindowsPath

from BossResolve import ResolvedBossState
from OrdinaryProfile import OrdinaryProfile
from PartFeatureIndex import EncodeFeatures, KConfiguration, KFeaturesXml, PartIndex
from PartInformation import EncodeInformation, KInfoXml, KMassName
from PartKeywords import EncodeKeywords, KDepth, KKeywordsXml
from convert.adapters.solidworks.Container.ArchiveCheck import RequireArch

KDisplayPlaces = Decimal("0.01")
KMillimetres = Decimal("1")
KInches = Decimal("25.4")


# the current save path and ordered index presentation are separate from model history
@dataclass(frozen=True, slots=True)
class PackageXmlState:
    SavedPath: str
    WidthFirst: bool
    Information: Mapping[str, str | int]


# both observed document unit settings store two decimal places and display magnitude
def DisplayScale(Information: Mapping[str, str | int]) -> Decimal:
    Fields = (
        Information["SW_UnitSystem"],
        Information["SW_UnitsLinear"],
        Information["SW_UnitsLinearDecimalDisplay"],
        Information["SW_UnitsLinearDecimalPlaces"],
        Information["SW_UnitsDecimalRounding"],
    )
    if Fields == (5, 0, 1, 2, 0):
        return KMillimetres
    RequireArch(Fields, (3, 3, 1, 2, 0), "ordinary keyword display units")
    return KInches


# display values are derived from already authored distances in document units
def DisplaySize(Millimetres: float, Scale: Decimal) -> Decimal:
    Display = abs(Decimal(str(Millimetres))) / Scale
    Rounded = Display.quantize(KDisplayPlaces, rounding=ROUND_HALF_UP)
    RequireArch(
        abs(Display - Rounded) != KDisplayPlaces / 2,
        True,
        "keyword display halfway rounding needs native evidence",
    )
    return Rounded


# the summaries reuse driver names and values and maintain the saved document relationship
def EncodePackageIndices(
    Generation: int,
    Identity: PartIndex,
    State: PackageXmlState,
    Profile: OrdinaryProfile,
    Boss: ResolvedBossState | None,
) -> dict[str, bytes]:
    Information = State.Information
    RequireArch(
        (
            Identity.SavedPath,
            Information.get("SW-File Name"),
            Information.get("SW-Configuration Name"),
            type(State.WidthFirst),
            KMassName in Information,
        ),
        (
            State.SavedPath,
            Identity.ModelName,
            KConfiguration,
            bool,
            Boss is not None,
        ),
        "shared ordinary document metadata and body state",
    )
    Scale = DisplayScale(Information)
    Width, Height = Profile.Lengths
    DisplayWidth = (Width.Name, DisplaySize(Width.Millimetres, Scale))
    DisplayHeight = (Height.Name, DisplaySize(Height.Millimetres, Scale))
    Drivers = (
        (DisplayWidth, DisplayHeight)
        if State.WidthFirst
        else (DisplayHeight, DisplayWidth)
    )
    DisplayBoss = None
    if Boss is not None:
        RequireArch(Boss.Display.NameValue, KDepth, "ordinary keyword Boss driver")
        DisplayBoss = (Boss.Opening.Name, DisplaySize(Boss.Display.DepthMm, Scale))
    return {
        KInfoXml: EncodeInformation(Generation, Information),
        KFeaturesXml: EncodeFeatures(Generation, Identity),
        KKeywordsXml: EncodeKeywords(
            Identity, Profile.Feature.Name, Drivers, DisplayBoss
        ),
    }


# the native feature model name belongs to the current filename rather than its prior reference
def MakePartIndex(
    SavedPath: str, Title: str, CreatedSeconds: int, LastModifiedStamp: int
) -> PartIndex:
    Path = PureWindowsPath(SavedPath)
    RequireArch(Path.suffix.lower(), ".sldprt", "ordinary part current filename")
    return PartIndex(CreatedSeconds, SavedPath, Path.stem, LastModifiedStamp, Title)
