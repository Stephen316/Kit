# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Generate the typed information-property table for ordinary SOLIDWORKS parts."""

from collections.abc import Mapping
from re import compile as Compile
from xml.etree.ElementTree import Element, SubElement

from PartFraming import VersionStorage
from PartOpc import EncodePackageXml, OFFICE_NS
from PartSectionProperties import KUserProps, KUtf8
from PartSimpleProperties import KVTypes

KInfoXml = "docProps/ISolidWorksInformation.xml"
KInfoNs = OFFICE_NS + "/SolidworksInformation-properties"
KMassName = "SW-MassProp-Config-0"
KInvalidXml = Compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")

# the two ordinary information layouts bind the same named document and unit slots
KInfoNames = (
    "SW-File Name",
    "SW-BOM Part Number",
    "SW-Folder Name",
    "SW-Short Date",
    "SW-Long Date",
    "SW-Configuration Name",
    "SW-Author",
    "SW-Keywords",
    "SW-Comments",
    "SW-Title",
    "SW-Subject",
    "SW-Created Date",
    "SW-Last Saved Date",
    "SW-Last Saved By",
    "SW-File Title",
    "V_WorldOrientation",
    "SW-HasDesignTable",
    "IsCPReArchEnabled",
    "SW_UnitSystem",
    "SW_UnitsLinear",
    "SW_UnitsLinearDecimalDisplay",
    "SW_UnitsLinearDecimalPlaces",
    "SW_UnitsLinearFractionDenominator",
    "SW_UnitsDualLinear",
    "SW_UnitsTimeUnits",
    "SW_UnitsPowerUnits",
    "SW_UnitsEnergyUnits",
    "SW_UnitsDualLinearDecimalDisplay",
    "SW_UnitsDualLinearDecimalPlaces",
    "SW_UnitsDualLinearFractionDenominator",
    "SW_UnitsAngular",
    "SW_UnitsAngularDecimalPlaces",
    "SW_UnitsMassPropLength",
    "SW_UnitsMassPropDecimalPlaces",
    "SW_UnitsMassPropMass",
    "SW_UnitsMassPropVolume",
    "SW_UnitsTimeDecimalPlaces",
    "SW_UnitsForce",
    "SW_UnitsForceDecimalPlaces",
    "SW_UnitsPowerDecimalPlaces",
    "SW_UnitsEnergyDecimalPlaces",
    "SW_UnitsDecimalRounding",
    "SW_UnitsLinearFeetAndInchesFormat",
    "SW_UnitsLinearRoundToNearestFraction",
    "SW_UnitsDualLinearRoundToNearestFraction",
    "SW_UnitsDualLinearFeetAndInchesFormat",
    "Component Type",
)

# the independently saved dictionary owns the presentation order and inserts mass after the long date
KDictOrder = (
    49,
    20,
    9,
    4,
    11,
    8,
    14,
    3,
    17,
    5,
    19,
    10,
    16,
    15,
    7,
    50,
    6,
    13,
    12,
    33,
    34,
    44,
    26,
    30,
    31,
    48,
    32,
    47,
    43,
    29,
    40,
    41,
    22,
    23,
    24,
    45,
    25,
    46,
    36,
    35,
    37,
    38,
    42,
    28,
    39,
    27,
    21,
    18,
)


# the native property slot decides its lexical variant before XML serialization
def TypedValue(Pid: int, Value: str | int) -> tuple[str, str]:
    if Pid in range(3, 18) or Pid == 50:
        if not isinstance(Value, str) or KInvalidXml.search(Value):
            raise ValueError(f"information property {Pid} requires valid XML text")
        return "lpstr", Value
    if type(Value) is not int or not -(1 << 31) <= Value < (1 << 31):
        raise ValueError(
            f"information property {Pid} requires a signed thirty two bit integer"
        )
    return "i4", str(Value)


# all emitted property records use native identifiers and a typed variant child
def AddProperty(Section: Element, Pid: int, PropName: str, Kind: str, Text: str):
    Row = SubElement(Section, "property", name=PropName, pid=str(Pid))
    SubElement(Row, "vt:" + Kind).text = Text


# the normal name and the summary alias intentionally share the same text property identifier
def AddDictionary(Section: Element, Names: Mapping[int, str]) -> None:
    SubElement(Section, "propertyNameDictionaryElement", name="", pid="0")
    for Pid in KDictOrder:
        if Pid == 50 and Pid not in Names:
            continue
        PropName = Names[Pid]
        SubElement(
            Section, "propertyNameDictionaryElement", name=PropName, pid=str(Pid)
        )
        if Pid in range(3, 18):
            Alias = f"{PropName}({PropName.removeprefix('SW-')})"
            SubElement(
                Section, "propertyNameDictionaryElement", name=Alias, pid=str(Pid)
            )


# typed caller values supply the saved source metadata and optional first configuration summary
def EncodeInformation(Generation: int, Values: Mapping[str, str | int]) -> bytes:
    VersionStorage(Generation)
    Names = dict(enumerate(KInfoNames, start=3))
    if KMassName in Values:
        Names[50] = KMassName
    if set(Values) != set(Names.values()):
        raise ValueError(
            "ordinary SOLIDWORKS information properties do not match the witnessed roster"
        )
    Root = Element("Properties", {"xmlns": KInfoNs, "xmlns:vt": KVTypes})
    Section = SubElement(
        Root,
        "propertySection",
        xmlns="",
        name="UserDefinedProperties",
        fmtid=KUserProps,
    )
    AddProperty(Section, 1, "", "i2", str(KUtf8))
    for Pid, PropName in Names.items():
        Kind, Text = TypedValue(Pid, Values[PropName])
        AddProperty(Section, Pid, PropName, Kind, Text)
    AddDictionary(Section, Names)
    return EncodePackageXml(Root, Standalone=True, ShortEmptyElements=False)
