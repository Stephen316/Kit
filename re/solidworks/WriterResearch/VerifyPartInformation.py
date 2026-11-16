# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Compare complete generated information properties with pinned licensed archives."""

from collections import Counter
from dataclasses import replace
from datetime import timezone
from hashlib import sha256
import json
from pathlib import PurePosixPath
from struct import unpack
from xml.etree.ElementTree import fromstring as ParseXml

from VerifyConfigRoot import CAPTURE_REVISION, principal_captures, require

from CmgrBaseHeader import ReadCmgrHeader
from CmgrBossMass import CalcBossMass, ReadBossMass
from CmgrColorReadback import ReadColorSpan
from CmgrInherited import ReadCmgrFeature
from ConfigUnits import ReadConfigUnits
from HeaderLogs import ReadHeaderLogs
from HeaderSelf import ReadHeaderSelf
from PartDocProperties import ReadCoreProperties, SummaryTime
from PartFraming import KPartGeneration
from PartInformation import EncodeInformation, KInfoXml, KInfoNs, KMassName
from PartInformationFields import (
    EncodePartInformation,
    InformationCalendar,
    InformationMass,
    InformationState,
    InformationSummary,
)
from PartSimpleProperties import KVTypes
from VerifyCmgrComposition import read_rectangular_boss
from VerifyConfigVisual import read_visual
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Container import SldprtArchive


# read the measured scalar values while the constructor owns every field position and alias
def TypedMetadata(Data):
    Root = ParseXml(Data)
    require(Root.tag == f"{{{KInfoNs}}}Properties", "native information root differs")
    (Section,) = list(Root)
    require(Section.tag == "propertySection", "native information section differs")
    Values = {}
    for Row in Section.findall("property"):
        Pid, Name = int(Row.attrib["pid"]), Row.attrib["name"]
        if Pid == 1:
            continue
        (Child,) = list(Row)
        require(Name not in Values, "duplicated native information property name")
        Typed = Child.tag
        if Typed == f"{{{KVTypes}}}i4":
            Values[Name] = int(Child.text)
        else:
            require(
                Typed == f"{{{KVTypes}}}lpstr",
                "unmodeled native information property variant",
            )
            Values[Name] = Child.text or ""
    return Values


# header, core properties, configuration settings and manager are independent of the information stream
def SourceState(Archive, Asset, Measurement, Layout):
    Generation = KPartGeneration
    Header, _ = ReadHeaderLogs(Archive.require("Header2"), Generation)
    File = ReadHeaderSelf(Header, Generation).File
    Core = ReadCoreProperties(Generation, Archive.require("docProps/core.xml"))
    Calendar = InformationCalendar(SummaryTime(Core.ModifiedTime).date(), timezone.utc)
    _, _, _, _, UnitsCursor, _, _ = read_visual(
        Archive.require("Contents/Config-0"), Generation, Layout
    )
    Units = ReadConfigUnits(UnitsCursor, Generation).Display

    NativeMass = None
    GeneratedMass = None
    _, _, BodyStamp = unpack("<3I", Archive.require("ModelStamps"))
    Boss = read_rectangular_boss(Archive, Generation, Measurement, BodyStamp)
    if Boss is not None:
        _, _, MassCursor = ReadColorSpan(Archive.require("Contents/CMgr"), Generation)
        ReadCmgrFeature(MassCursor, Generation)
        ReadCmgrHeader(MassCursor, Generation)
        NativeMass = ReadBossMass(MassCursor, Generation, 1)
        GeneratedMass = CalcBossMass(Boss.MinimumM, Boss.MaximumM, Boss.DensityKgM3)
    return (
        InformationState(
            OutputPath=PurePosixPath(Asset["path"]).name,
            File=File,
            Core=Core,
            Calendar=Calendar,
            Summary=InformationSummary("", "", "", "", "", ""),
            Units=Units,
            ZUp=False,
            HasDesignTable=False,
            ModernProperties=True,
            Mass=NativeMass,
        ),
        GeneratedMass,
    )


# generated solid properties can differ from the kernel only in the sign of displayed zero products
def CompareCalculated(Native, Calculated):
    NativeFields = Native.split(", ")
    CalculatedFields = InformationMass(Calculated).split(", ")
    require(len(NativeFields) == len(CalculatedFields) == 14, "mass field count")
    for Index in (9, 10, 11):
        require(
            float(NativeFields[Index]) == float(CalculatedFields[Index]) == 0.0,
            "rectangular solid inertia product",
        )
        NativeFields[Index] = CalculatedFields[Index]
    require(NativeFields == CalculatedFields, "authored cuboid mass XML values")
    return ", ".join(NativeFields)


# compare full encoded streams and record only stable source and output hashes
def report():
    Cases = {}
    Counts = Counter()
    TotalWithMass = 0
    SourceConstructed = 0
    GeometryConstructed = 0
    Layout = LoadPartLayouts().Prefix
    for Recipe, Asset, Raw, _, Measurement in principal_captures():
        Archive = SldprtArchive.from_bytes(Raw, Asset["path"])
        Source = Archive.require(KInfoXml)
        Values = TypedMetadata(Source)
        require(
            (KMassName in Values) == (Recipe == "P03"),
            "unexpected mass metadata layout",
        )
        Output = EncodeInformation(KPartGeneration, Values)
        require(
            Output == Source,
            f"complete typed information property stream differs: {Asset['sha256']}",
        )
        State, Calculated = SourceState(Archive, Asset, Measurement, Layout)
        Sourced = EncodePartInformation(KPartGeneration, State)[KInfoXml]
        require(
            Sourced == Source,
            f"independent information fields differ: {Asset['sha256']}",
        )
        SourceConstructed += 1
        if Calculated is not None:
            Expected = dict(Values)
            Expected[KMassName] = CompareCalculated(Values[KMassName], Calculated)
            Generated = EncodePartInformation(
                KPartGeneration, replace(State, Mass=Calculated)
            )[KInfoXml]
            require(
                Generated == EncodeInformation(KPartGeneration, Expected),
                f"authored geometry information stream differs: {Asset['sha256']}",
            )
            GeometryConstructed += 1
        Counts[Recipe] += 1
        TotalWithMass += KMassName in Values
        Cases[Asset["sha256"]] = sha256(Output).hexdigest()
    require(Counts == {"P01": 6, "P03": 8}, "unexpected native information captures")
    return {
        "capture_revision": CAPTURE_REVISION,
        "captures": Cases,
        "counts": dict(Counts),
        "with_mass_summary": TotalWithMass,
        "source_constructed": SourceConstructed,
        "geometry_constructed": GeometryConstructed,
        "replay_sha256": sha256(
            json.dumps(Cases, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    print(json.dumps(report(), sort_keys=True))
