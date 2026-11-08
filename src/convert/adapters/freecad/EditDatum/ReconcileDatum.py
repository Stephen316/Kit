# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from collections.abc import Mapping
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from convert.adapters.base import ParseUntrusted
from convert.adapters.freecad.Archive import BuildDocXmlMut
from convert.adapters.freecad.EditBinding import ReadEditBinding
from convert.adapters.freecad.EditDatum.DatumBinding import KDatumBinding, KDatumGroup
from convert.adapters.freecad.EditDatum.DatumSavedArchive import CheckDatumFiles
from convert.adapters.freecad.EditDatum.DatumSavedGraph import ReadDatumGraph
from convert.adapters.freecad.EditDatum.DatumSavedValues import (
    ApplyDatumVals,
    ReadDatumParams,
)
from convert.adapters.freecad.EditPlaneRev.PlaneRevBinding import KPlaneRevBinding
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureBoundPlane import BoundConstructionPlane


# legacy static planes and separately reconciled revolve planes are outside this binding
def HasDatumTrace(RootValue: Element, PlaneIds: set[str]) -> bool:
    if not PlaneIds:
        return False
    if RootValue.find(f"./Objects/Object[@name='{KDatumGroup}']") is not None:
        return True
    Names = {
        Value.get("name")
        for Value in RootValue.findall("./Objects/Object[@type='App::Plane']")
    }
    IsRevolve = ReadEditBinding(RootValue, KPlaneRevBinding) is not None
    for Value in RootValue.findall("./ObjectData/Object"):
        if Value.get("name") not in Names:
            continue
        Properties = Value.find("./Properties")
        if Properties is None:
            continue
        if any(
            Properties.find(f"./Property[@name='{Field}']") is not None
            for Field in ("KitFeatureId", "SourceFeatureJSON")
        ):
            return True
        Identity = Properties.find("./Property[@name='KitId']/String")
        if (
            not IsRevolve
            and Identity is not None
            and Identity.get("value") in PlaneIds
            and Properties.find(
                "./Property[@name='ExpressionEngine']/ExpressionEngine/Expression[@path='Placement']"
            )
            is not None
        ):
            return True
    return False


# a native datum save can replace source parameters only after the full graph is verified
def ReconcileDatum(
    Document: CadDocument,
    Manifest: Mapping[str, object],
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue, KDatumBinding)
    Controls = tuple(
        (Value, Definition)
        for Value in Document.feature_timeline
        if isinstance(Definition := Value.definition, BoundConstructionPlane)
    )
    PlaneIds = {Definition.SupportPlaneId for _, Definition in Controls}
    if Binding is None:
        if HasDatumTrace(RootValue, PlaneIds):
            raise ValueError("FreeCAD editable datum binding is missing")
        return Document
    if Binding != KDatumGroup or not Controls or len(PlaneIds) != len(Controls):
        raise ValueError("FreeCAD editable datum binding disagrees with its source")
    Features: set[str] = set()
    XmlData, Entries = BuildDocXmlMut(Manifest, "", "", EditableFeatures=Features)
    if Features != {Value.id for Value, _ in Controls}:
        raise ValueError("FreeCAD editable datum source timeline is unresolved")
    Template = ParseUntrusted(XmlData)
    if ReadEditBinding(Template, KDatumBinding) != Binding:
        raise ValueError("FreeCAD editable datum source graph is unresolved")
    CheckDatumFiles(RootValue, Archive, Members, Entries)
    Native, Original, Pending = ReadDatumGraph(RootValue, Template)
    Editable = {Definition.ScalarParameterId for _, Definition in Controls}
    Parameters = ReadDatumParams(
        Document, Manifest, Native["Parameters"], Original["Parameters"], Editable
    )
    if Pending and Parameters != Document.parameters:
        raise ValueError("FreeCAD editable datum native rebuild is pending")
    return ApplyDatumVals(Document, Controls, Native, Parameters)
