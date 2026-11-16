# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Construct the ordinary app, core and open-time property members."""

from dataclasses import dataclass as Dataclass
from datetime import datetime as DateTime, timedelta as TimeDelta
from re import fullmatch as FullMatch

from PartManifests import EncodeXml, KOffice, KPackage

KAppProps = "docProps/app.xml"
KCoreProps = "docProps/core.xml"
KOpenProps = "docProps/OpenTime.xml"
KDecl = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
KVTypes = KOffice + "/docPropsVTypes"


# application presentation fields are retained exactly as supplied by the document owner
@Dataclass(frozen=True, slots=True)
class AppProperties:
    TemplateName: str
    TotalTime: int
    Application: str
    DocSecurity: int
    Company: str
    LinkIndex: bool
    SharedDoc: bool
    Hyperlinks: bool
    AppVersion: str


# core properties retain the caller's archival modification identity and UTC chronology
@Dataclass(frozen=True, slots=True)
class CoreProperties:
    Modifier: str
    Created: DateTime
    Modified: DateTime


# counters and optional formatted values retain the saved open-time records
@Dataclass(frozen=True, slots=True)
class OpenProperties:
    Count: int
    Total: int
    LightCount: int
    LightTotal: int
    DisplayTime: str | None = None


# both property bodies use ordinary standalone document framing and escaped text attributes
def EncodeSimple(Namespace, Entries):
    return EncodeXml(
        KDecl, "Properties", {"xmlns": Namespace, "xmlns:vt": KVTypes}, Entries
    )


# the package declares these native metadata fields in a stable recorded order
def EncodeAppProps(State: AppProperties) -> bytes:
    if type(State.TotalTime) is not int or type(State.DocSecurity) is not int:
        raise ValueError("app counters require integers")
    Flags = (State.LinkIndex, State.SharedDoc, State.Hyperlinks)
    if any(type(Value) is not bool for Value in Flags):
        raise ValueError("app flags require Booleans")
    return EncodeSimple(
        KOffice + "/extended-properties",
        (
            ("Template", {}, State.TemplateName),
            ("TotalTime", {}, str(State.TotalTime)),
            ("Application", {}, State.Application),
            ("DocSecurity", {}, str(State.DocSecurity)),
            ("Company", {}, State.Company),
            ("LinksUpToDate", {}, str(State.LinkIndex).lower()),
            ("SharedDoc", {}, str(State.SharedDoc).lower()),
            ("HyperlinksChanged", {}, str(State.Hyperlinks).lower()),
            ("AppVersion", {}, State.AppVersion),
        ),
    )


# the recorded core properties use whole-second UTC timestamps
def EncodeStamp(Value: DateTime) -> str:
    if (
        not isinstance(Value, DateTime)
        or Value.utcoffset() != TimeDelta(0)
        or Value.microsecond
    ):
        raise ValueError("core property timestamps require whole UTC seconds")
    return Value.isoformat(timespec="seconds").removesuffix("+00:00") + "Z"


# core timestamps are separate fields from application version and save metadata
def EncodeCoreProps(State: CoreProperties) -> bytes:
    return EncodeXml(
        KDecl,
        "cp:coreProperties",
        {
            "xmlns:cp": KPackage + "/metadata/core-properties",
            "xmlns:dc": "http://purl.org/dc/elements/1.1/",
            "xmlns:dcterms": "http://purl.org/dc/terms/",
            "xmlns:dcmitype": "http://purl.org/dc/dcmitype/",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        },
        (
            ("dc:lastModifiedBy", {}, State.Modifier),
            ("dcterms:created", {}, EncodeStamp(State.Created)),
            ("dcterms:modified", {}, EncodeStamp(State.Modified)),
        ),
    )


# incomplete historical open telemetry is represented by its saved total sentinel
def EncodeOpenProps(State: OpenProperties) -> bytes:
    Counts = (State.Count, State.LightCount)
    Totals = (State.Total, State.LightTotal)
    if any(type(Value) is not int or Value < 0 for Value in Counts) or any(
        type(Value) is not int or Value < -1 for Value in Totals
    ):
        raise ValueError("invalid saved open counters or totals")
    Fields = {"xmlns": ""}
    Entries = [
        ("count", Fields, str(State.Count)),
        ("TotalFileOpenTime", Fields, str(State.Total)),
        ("LWcount", Fields, str(State.LightCount)),
        ("LWTotalFileOpenTime", Fields, str(State.LightTotal)),
    ]
    if State.DisplayTime is not None:
        if not FullMatch(r"[0-9]+:[0-5][0-9]", State.DisplayTime):
            raise ValueError("invalid saved file open time display")
        Entries.append(("FileOpenTime", Fields, State.DisplayTime))
    return EncodeSimple(KOffice + "/SolidworksOpenTime", Entries)
