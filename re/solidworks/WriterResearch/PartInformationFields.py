# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Derive standalone part information values from independent document state."""

from dataclasses import dataclass
from datetime import date, tzinfo
from math import isfinite
from pathlib import PureWindowsPath

from CmgrBossMass import BossMass, BossMassFields
from CmgrExternal import ExternalFile
from ConfigUnitFields import KDisplayProfiles, KFormats, UnitDisplay
from PartDocProperties import CoreProperties, SummaryTime
from PartInformation import EncodeInformation, KInfoXml, KMassName
from convert.adapters.solidworks.Container.Format import KPartSuffix

ENGLISH_MONTHS = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)


@dataclass(frozen=True, slots=True)
class InformationCalendar:
    LocalDate: date
    LocalZone: tzinfo


@dataclass(frozen=True, slots=True)
class InformationSummary:
    Author: str
    Keywords: str
    Comments: str
    Title: str
    Subject: str
    FileTitle: str


@dataclass(frozen=True, slots=True)
class InformationState:
    OutputPath: str
    File: ExternalFile
    Core: CoreProperties
    Calendar: InformationCalendar
    Summary: InformationSummary
    Units: UnitDisplay
    ZUp: bool
    HasDesignTable: bool
    ModernProperties: bool
    Mass: BossMass | None


def EnglishDate(Day: date) -> str:
    return f"{Day.day} {ENGLISH_MONTHS[Day.month - 1]} {Day.year:04d}"


def EnglishDateTime(Seconds: int, LocalZone: tzinfo) -> str:
    Local = SummaryTime(Seconds).astimezone(LocalZone)
    return (
        f"{EnglishDate(Local)} {Local.hour:02d}:{Local.minute:02d}:{Local.second:02d}"
    )


# File Name is the current output; Folder Name is the prior document reference.
def InformationDocument(State: InformationState) -> dict[str, str | int]:
    Path = PureWindowsPath(State.OutputPath)
    if Path.suffix.casefold() != KPartSuffix or not Path.stem:
        raise ValueError("information requires a SOLIDWORKS part output path")
    Reference = State.File.FilePath
    Folder = ""
    if Reference:
        Parent = str(PureWindowsPath(Reference).parent)
        if Parent != ".":
            Folder = Parent.rstrip("\\") + "\\"
    Calendar = State.Calendar
    Today = Calendar.LocalDate
    Core = State.Core
    Summary = State.Summary
    if type(Today) is not date or not isinstance(Calendar.LocalZone, tzinfo):
        raise ValueError(
            "information requires an explicit local calendar and time zone"
        )
    if type(State.ZUp) is not bool:
        raise ValueError("information requires an explicit world orientation")
    if State.HasDesignTable is not False or State.ModernProperties is not True:
        raise ValueError(
            "information supports ordinary standalone parts with modern properties"
        )
    return {
        "SW-File Name": Path.stem,
        "SW-BOM Part Number": State.File.Title,
        "SW-Folder Name": Folder,
        "SW-Short Date": f"{Today.day:02d}/{Today.month:02d}/{Today.year:04d}",
        "SW-Long Date": EnglishDate(Today),
        "SW-Configuration Name": State.File.ConfigName,
        "SW-Author": Summary.Author,
        "SW-Keywords": Summary.Keywords,
        "SW-Comments": Summary.Comments,
        "SW-Title": Summary.Title,
        "SW-Subject": Summary.Subject,
        "SW-Created Date": EnglishDateTime(Core.CreatedTime, Calendar.LocalZone),
        "SW-Last Saved Date": EnglishDateTime(Core.ModifiedTime, Calendar.LocalZone),
        "SW-Last Saved By": Core.LastModifiedBy,
        "SW-File Title": Summary.FileTitle,
        "V_WorldOrientation": int(not State.ZUp),
        "SW-HasDesignTable": int(State.HasDesignTable),
        "IsCPReArchEnabled": int(State.ModernProperties),
        "Component Type": 0,
    }


# The information preferences expose length and angle selectors directly, and
# expose the active system, force, energy, mass and volume as one-based codes.
def InformationUnits(Display: UnitDisplay) -> dict[str, int]:
    if Display not in KDisplayProfiles:
        raise ValueError(
            "information units require the measured metric or inch profile"
        )
    return {
        "SW_UnitSystem": Display.System + 1,
        "SW_UnitsLinear": Display.Length,
        "SW_UnitsLinearDecimalDisplay": 1,
        "SW_UnitsLinearDecimalPlaces": 2,
        "SW_UnitsLinearFractionDenominator": KFormats["primary"][2],
        "SW_UnitsDualLinear": 3,
        "SW_UnitsTimeUnits": 1,
        "SW_UnitsPowerUnits": 1,
        "SW_UnitsEnergyUnits": Display.Energy + 1,
        "SW_UnitsDualLinearDecimalDisplay": 1,
        "SW_UnitsDualLinearDecimalPlaces": 2,
        "SW_UnitsDualLinearFractionDenominator": KFormats["dual"][2],
        "SW_UnitsAngular": 0,
        "SW_UnitsAngularDecimalPlaces": 2,
        "SW_UnitsMassPropLength": 0,
        "SW_UnitsMassPropDecimalPlaces": 2,
        "SW_UnitsMassPropMass": Display.DensityMass + 1,
        "SW_UnitsMassPropVolume": Display.DensityVolume + 1,
        "SW_UnitsTimeDecimalPlaces": 2,
        "SW_UnitsForce": Display.Force + 1,
        "SW_UnitsForceDecimalPlaces": 2,
        "SW_UnitsPowerDecimalPlaces": 2,
        "SW_UnitsEnergyDecimalPlaces": 2,
        "SW_UnitsDecimalRounding": 0,
        "SW_UnitsLinearFeetAndInchesFormat": 1,
        "SW_UnitsLinearRoundToNearestFraction": 0,
        "SW_UnitsDualLinearRoundToNearestFraction": 0,
        "SW_UnitsDualLinearFeetAndInchesFormat": 1,
    }


# The ordinary calculated mass record uses SI and the positive tensor convention.
def InformationMass(Value: BossMass) -> str:
    Fields = BossMassFields(Value)
    if (
        len(Fields) != 12
        or not all(isfinite(Field) for Field in Fields)
        or not all(Field > 0 for Field in Fields[3:9])
    ):
        raise ValueError("information mass requires finite calculated solid properties")
    Tensor = (*Fields[:9], *(-Product for Product in Fields[9:]))
    return ", ".join((*(f"{Field:.16f}" for Field in Tensor), "1.000000", "0.000000"))


def EncodePartInformation(Generation: int, State: InformationState) -> dict[str, bytes]:
    Values = InformationDocument(State)
    Values.update(InformationUnits(State.Units))
    if State.Mass is not None:
        Values[KMassName] = InformationMass(State.Mass)
    return {KInfoXml: EncodeInformation(Generation, Values)}
