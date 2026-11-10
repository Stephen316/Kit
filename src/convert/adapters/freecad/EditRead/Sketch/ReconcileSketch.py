# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from interchange.records.RecordParameter import Parameter
from interchange.geometry.models.Transform import Transform
from convert.adapters.freecad.Native import NativeObject
from collections.abc import Mapping
from dataclasses import replace as Replace
from xml.etree.ElementTree import Element
from zipfile import ZipFile, ZipInfo

from convert.adapters.base import ParseUntrusted
from convert.adapters.freecad.Archive import BuildDocXmlMut, Items, ParamCatalog
from convert.adapters.freecad.EditBinding import ReadEditBinding
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.Sketch.SavedSketchGeom import ReadSketchGeom
from convert.adapters.freecad.EditRead.Sketch.SavedSketchRules import CheckSavedRules
from convert.adapters.freecad.EditRead.Sketch.SketchEvidence import (
    CheckCarriers,
    CheckSketchFile,
)
from convert.adapters.freecad.EditRead.Sketch.SketchGraph import (
    IndexSketchObjs,
    ReadSketchGraph,
)
from convert.adapters.freecad.EditRead.Sketch.SketchParams import (
    KeepSketchRef,
    ReadSketchVals,
)
from convert.adapters.freecad.EditSketchPlan import KSketchEditBinding, ReadSketchPlan
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Sketch import Sketch


# bound sketch edits replace only the geometry and values that native records corroborate
def ReconcileSketch(
    Document: CadDocument,
    Manifest: Mapping[str, object],
    RootValue: Element,
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> CadDocument:
    Binding = ReadEditBinding(RootValue, KSketchEditBinding)
    if Binding is None:
        return Document
    Drivers = ReadSketchPlan(Document)
    if Binding != "Sketches" or Drivers is None:
        raise ValueError("FreeCAD editable sketch binding disagrees with its source")
    Template, _ = BuildDocXmlMut(Manifest, "", "")
    Objects, Expected = ReadSketchGraph(RootValue, ParseUntrusted(Template))
    CheckCarriers(Objects, Members)
    Catalog = ParamCatalog(Items(Manifest.get("parameters", [])))
    Parameters = ReadSketchVals(
        Objects["Parameters"], Catalog, Document.parameters, Drivers
    )
    Planes = {Value.id: Value.transform for Value in Document.support_planes}
    Sketches: list[Sketch] = []
    NativeObjects = IndexSketchObjs(Objects.values())
    for Original in Document.sketches:
        Edited = ReadSketchMut(
            Original, NativeObjects, Expected, Planes, Parameters, Archive, Members
        )
        Sketches.append(Edited)
    FinalParams = tuple(Parameters[Value.id] for Value in Document.parameters)
    FinalSketches = tuple(Sketches)
    if FinalParams == Document.parameters and FinalSketches == Document.sketches:
        return Document
    return Replace(Document, parameters=FinalParams, sketches=FinalSketches)


# an editable sketch updates reference measures only after its native geometry is verified
def ReadSketchMut(
    Original: Sketch,
    NativeObjects: dict[str, NativeObject],
    Expected: dict[str, NativeObject],
    Planes: dict[str, Transform],
    Parameters: dict[str, Parameter],
    Archive: ZipFile,
    Members: Mapping[str, ZipInfo],
) -> Sketch:
    Native = NativeObjects.get(Original.id)
    Plane = NativeObjects.get(Original.support_plane_id)
    if (
        Native is None
        or Native.type_id != "Sketcher::SketchObject"
        or Plane is None
        or Plane.type_id != "App::Plane"
    ):
        raise ValueError("FreeCAD editable sketch or support identity is missing")
    Frame = Planes[Original.support_plane_id]
    CheckEditFrame(Native, "Placement", Frame)
    CheckEditFrame(Plane, "Placement", Frame)
    Edited = ReadSketchGeom(Native, Original)
    References = CheckSavedRules(
        Native,
        Expected[Native.name].properties["Constraints"],
        Original,
        Edited,
        Parameters,
    )
    CheckSketchFile(Archive, Members, Native, Original, Edited, Frame)
    for ParamId, Measure in References.items():
        Parameters[ParamId] = KeepSketchRef(Parameters[ParamId], Measure)
    return Edited
