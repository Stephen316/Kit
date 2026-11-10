# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from collections.abc import Mapping
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import tostring as XmlBytes

from zipfile import ZipFile, ZipInfo

from convert.adapters.base.SafeParsing import ParseUntrusted
from convert.adapters.freecad.Archive import BuildDocXmlMut
from convert.adapters.freecad.EditBinding import ReadEditBinding
from convert.adapters.freecad.EditScale.ScaleBinding import KScaleBinding
from convert.adapters.freecad.EditScale.ScaleWritePlan import ReadScalePlan
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBoundScale import BoundScale


# compare generated native data independently of the embedded manifest carrier text
def ScaleGraph(RootValue: Element) -> tuple[bytes, ...]:
    Sections = tuple(
        XmlBytes(Value)
        for TagValue in ("Objects", "ObjectDeps")
        if (Value := RootValue.find(TagValue)) is not None
    )
    return Sections + tuple(
        XmlBytes(Value)
        for Value in RootValue.findall("./ObjectData/Object")
        if Value.get("name") != "KitMetadata"
    )


# native saved edits and pristine seed archives require different geometry witnesses
def ReconcileScale(
    Document: CadDocument,
    Manifest: Mapping[str, object],
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue, KScaleBinding)
    Feature = Document.feature_timeline[-1] if Document.feature_timeline else None
    Definition = None if Feature is None else Feature.definition
    if Binding is None and not isinstance(Definition, BoundScale):
        return Document
    NativeScale = RootValue.find("./Objects/Object[@type='Part::Scale']") is not None
    if (
        Binding is None
        and not NativeScale
        and RootValue.find(
            "./ObjectData/Object/Properties/Property[@name='KitFeatureId']"
        )
        is None
    ):
        return Document
    if (
        Feature is None
        or not isinstance(Definition, BoundScale)
        or Binding != Feature.id
        or not NativeScale
    ):
        raise ValueError("FreeCAD editable Scale binding disagrees with its source")
    Features: set[str] = set()
    Expected, Entries = BuildDocXmlMut(Manifest, "", "", EditableFeatures=Features)
    if Feature.id not in Features:
        raise ValueError("FreeCAD editable Scale source timeline is unresolved")
    Template = ParseUntrusted(Expected)
    if ScaleGraph(RootValue) != ScaleGraph(Template):
        from convert.adapters.freecad.EditScale.ScaleSavedRead import ReadSavedScale

        return ReadSavedScale(
            Document,
            Manifest,
            Feature,
            Definition,
            ReadScalePlan(Document, Feature, Definition),
            Template,
            RootValue,
            Archive,
            Members,
        )
    Shapes = {
        NameValue: DataValue
        for NameValue, DataValue in Entries.items()
        if NameValue.lower().endswith(".brp")
    }
    if set(Shapes) != {
        NameValue for NameValue in Members if NameValue.lower().endswith(".brp")
    } or any(
        Members[NameValue].file_size != len(DataValue)
        or Archive.read(Members[NameValue]) != DataValue
        for NameValue, DataValue in Shapes.items()
    ):
        raise ValueError("FreeCAD editable Scale saved shape disagrees with its source")
    return Document
