# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.EditSketch import CheckEditSketch
from convert.adapters.freecad.EditRead.XmlField import (
    CheckEditExpr,
    CheckNoEditExpr,
    EditChild,
    EditScalar,
    OnlyEditChild,
)
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform


# a linked sketch may seed a depth edit only while its geometry and support remain unchanged
def CheckEditProf(
    Objects: tuple[NativeObject, ...],
    Feature: NativeObject,
    SketchValue: Sketch,
    PlaneValue: SupportPlane,
) -> None:
    Sketch = RequireEditObj(Objects, SketchValue.id, "Sketcher::SketchObject")
    Plane = RequireEditObj(Objects, PlaneValue.id, "App::Plane")
    if (
        EditScalar(Feature, "Base", "App::PropertyLink", "Link") != Sketch.name
        or EditScalar(Sketch, "SupportPlane", "App::PropertyLink", "Link") != Plane.name
    ):
        raise ValueError("FreeCAD editable extrusion profile or support link changed")
    Attachment = EditChild(
        Sketch, "AttachmentSupport", "App::PropertyLinkSubList", "LinkSubList"
    )
    LinkValue = OnlyEditChild(Attachment, "Link")
    if (
        Attachment.get("count") != "1"
        or LinkValue.get("obj") != Plane.name
        or LinkValue.get("sub") != ""
    ):
        raise ValueError("FreeCAD editable sketch attachment changed")
    CheckEditExpr(Sketch, "Placement", f"{Plane.name}.Placement")
    CheckEditFrame(Sketch, "Placement", PlaneValue.transform)
    CheckEditFrame(Plane, "Placement", PlaneValue.transform)
    CheckNoEditExpr(Plane)
    CheckEditFrame(Sketch, "AttachmentOffset", Transform(), Optional=True)
    for Field, KindValue, TagName, Expected in (
        ("MapMode", "App::PropertyEnumeration", "Integer", "0"),
        ("MapReversed", "App::PropertyBool", "Bool", "false"),
    ):
        if (
            Field in Sketch.properties
            and EditScalar(Sketch, Field, KindValue, TagName) != Expected
        ):
            raise ValueError(f"FreeCAD editable sketch {Field} changed")
    CheckEditSketch(Sketch, SketchValue)
