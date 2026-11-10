# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.freecad.EditRead.EditObjects import RequireEditObj
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.EditSketch import CheckEditSketch
from convert.adapters.freecad.EditRead.Sketch.ProfileProof import ReadEditProfile
from convert.adapters.freecad.EditRead.Sketch.RingProof import ReadRingProfile
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


# independent and driving sketches share an exact support and placement contract
def CheckEditPlane(
    Sketch: NativeObject,
    Plane: NativeObject,
    PlaneValue: SupportPlane,
) -> None:
    if EditScalar(Sketch, "SupportPlane", "App::PropertyLink", "Link") != Plane.name:
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


# a linked sketch may seed a depth edit only while its geometry and support remain unchanged
def CheckEditProf(
    Objects: tuple[NativeObject, ...],
    Feature: NativeObject,
    SketchValue: Sketch,
    PlaneValue: SupportPlane,
    AllowProfile: bool = False,
    LineRing: bool = False,
) -> Sketch:
    Sketch = RequireEditObj(Objects, SketchValue.id, "Sketcher::SketchObject")
    Plane = RequireEditObj(Objects, PlaneValue.id, "App::Plane")
    if EditScalar(Feature, "Base", "App::PropertyLink", "Link") != Sketch.name:
        raise ValueError("FreeCAD editable extrusion profile or support link changed")
    CheckEditPlane(Sketch, Plane, PlaneValue)
    if LineRing:
        return ReadRingProfile(Sketch, SketchValue, AllowProfile)
    if AllowProfile:
        return ReadEditProfile(Sketch, SketchValue)
    CheckEditSketch(Sketch, SketchValue)
    return SketchValue
