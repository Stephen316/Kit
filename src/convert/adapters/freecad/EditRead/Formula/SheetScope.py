# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.Formula.SheetScaffold import (
    CheckEmptyProxy,
    CheckGroupState,
    CheckLinkList,
    CheckProperties,
    CheckSheetCfg,
    CheckSheetDeps,
)
from convert.adapters.freecad.EditRead.XmlField import EditScalar
from convert.adapters.freecad.FormulaSheet.SheetBinding import KFormulaSheetBinding
from convert.adapters.freecad.Native import NativeObject, ParseObjects

# these scaffolding groups are the complete native graph outside of the spreadsheet and metadata
KSheetGroupNames = frozenset(
    {
        "SupportPlanes",
        "Sketches",
        "Selections",
        "Configurations",
        "FeatureTimeline",
        "Bodies",
    }
)

# the saved spreadsheet may keep display layout but no linked files or modeling properties
KSheetFields = {
    "cells": "Spreadsheet::PropertySheet",
    "columnWidths": "Spreadsheet::PropertyColumnWidths",
    "rowHeights": "Spreadsheet::PropertyRowHeights",
}

# the embedded source snapshot and binding are the only persistent kit metadata in scope
KMetadataFields = {
    "KitManifestEncoding": "App::PropertyString",
    "KitManifestSHA256": "App::PropertyString",
    "KitManifestData": "App::PropertyString",
    "SchemaVersion": "App::PropertyString",
    "ParameterAliasesJSON": "App::PropertyString",
    "FinalFeature": "App::PropertyString",
    "ExternalLinkTarget": "App::PropertyString",
    "CachedShapeEntry": "App::PropertyString",
    "AssemblyRoot": "App::PropertyString",
    "AssemblyOccurrenceCount": "App::PropertyInteger",
    "AssemblyMateCount": "App::PropertyInteger",
    "NativePayloadEntries": "App::PropertyStringList",
    "Proxy": "App::PropertyPythonObject",
    KFormulaSheetBinding: "App::PropertyString",
}

# the single projected configuration keeps no model features or parameter overrides
KConfigFields = {
    "KitConfigurationId": "App::PropertyString",
    "Active": "App::PropertyBool",
    "SuppressedFeatures": "App::PropertyLinkList",
    "Parameters": "App::PropertyLink",
    "ParameterOverridesJSON": "App::PropertyString",
    "SourceConfigurationJSON": "App::PropertyString",
    "Proxy": "App::PropertyPythonObject",
}


# group memberships and bodies links can only reference the generated document scaffolding
def CheckSheetGroup(ObjectValue: NativeObject) -> None:
    Fields = {"Group": "App::PropertyLinkList"}
    Links = ("Sketches", "FeatureTimeline") if ObjectValue.name == "Bodies" else ()
    Members = ("History_projection",) if ObjectValue.name == "Configurations" else ()
    for NameValue in Links:
        Fields[NameValue] = "App::PropertyLink"
        if EditScalar(ObjectValue, NameValue, "App::PropertyLink", "Link") != NameValue:
            raise ValueError("FreeCAD editable spreadsheet scaffold link changed")
    CheckProperties(ObjectValue, Fields)
    CheckLinkList(ObjectValue, "Group", Members)
    CheckSheetDeps(ObjectValue, (*Members, *Links))
    CheckGroupState(ObjectValue)


# metadata cannot claim a geometry cache or executable feature in an editable workbook
def CheckSheetMeta(ObjectValue: NativeObject) -> None:
    CheckProperties(ObjectValue, KMetadataFields)
    CheckEmptyProxy(ObjectValue)
    for NameValue in ("FinalFeature", "CachedShapeEntry", "AssemblyRoot"):
        if EditScalar(ObjectValue, NameValue, "App::PropertyString", "String"):
            raise ValueError(
                "FreeCAD editable spreadsheet metadata declares native geometry"
            )
    for NameValue in ("AssemblyOccurrenceCount", "AssemblyMateCount"):
        if EditScalar(ObjectValue, NameValue, "App::PropertyInteger", "Integer") != "0":
            raise ValueError(
                "FreeCAD editable spreadsheet metadata declares an assembly"
            )
    if (
        EditScalar(ObjectValue, "ExternalLinkTarget", "App::PropertyString", "String")
        != "Bodies"
    ):
        raise ValueError("FreeCAD editable spreadsheet metadata target changed")


# unexpected native objects could carry feature geometry that the source workbook cannot retain
def ReadSheetObject(RootValue: Element) -> NativeObject:
    Objects = {Value.name: Value for Value in ParseObjects(RootValue)}
    Types = {
        **dict.fromkeys(KSheetGroupNames, "App::DocumentObjectGroup"),
        "Parameters": "Spreadsheet::Sheet",
        "KitMetadata": "App::FeaturePython",
        "History_projection": "App::FeaturePython",
    }
    if Objects.keys() != Types.keys() or any(
        Value.type_id != Types[NameValue] for NameValue, Value in Objects.items()
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet has an additional or changed native object"
        )
    for NameValue in KSheetGroupNames:
        CheckSheetGroup(Objects[NameValue])
    Sheet = Objects["Parameters"]
    Metadata = Objects["KitMetadata"]
    Config = Objects["History_projection"]
    if any(
        Value.extensions or Value.transient_properties
        for Value in (Sheet, Metadata, Config)
    ):
        raise ValueError(
            "FreeCAD editable spreadsheet has additional native extensions"
        )
    CheckProperties(Sheet, KSheetFields)
    CheckSheetMeta(Metadata)
    CheckProperties(Config, KConfigFields)
    CheckEmptyProxy(Config)
    CheckSheetCfg(Config)
    CheckSheetDeps(Sheet, ())
    CheckSheetDeps(Metadata, ())
    CheckSheetDeps(Config, ("Parameters",))
    return Sheet
