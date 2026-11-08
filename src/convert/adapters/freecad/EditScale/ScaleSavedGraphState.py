# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditRead.EditExtrusion import (
    CheckEditMaker,
    CheckEditOpts,
)
from convert.adapters.freecad.EditRead.EditPlacement import CheckEditFrame
from convert.adapters.freecad.EditRead.Formula.SheetScaffold import CheckEmptyProxy
from convert.adapters.freecad.EditRead.Sketch.SavedExternal import CheckExternal
from convert.adapters.freecad.EditRead.Sketch.SketchDefaults import (
    CheckExtensions,
    CheckSketchOpts,
    KSketchObjExtra,
)
from convert.adapters.freecad.EditRead.XmlField import (
    EditChild,
    EditScalar,
    OnlyEditChild,
)
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.Transform import KTransformIdentity

# native built in defaults are the only properties absent from the generated graph
KCommonExtras = {
    "ExpressionEngine": "App::PropertyExpressionEngine",
    "Label2": "App::PropertyString",
}

# these properties belong to native scale controls rather than neutral feature metadata
KScaleExtras = {
    "Part::Scale": {"ShapeMaterial": "Materials::PropertyMaterial"},
    "App::Point": {"Role": "App::PropertyString"},
}


# native added fields must have only the built in types from the supported save grammar
def ExtraScaleType(TypeName: str, NameValue: str) -> str | None:
    return KScaleExtras.get(TypeName, KSketchObjExtra.get(TypeName, {})).get(
        NameValue, KCommonExtras.get(NameValue)
    )


# new native defaults cannot disguise a dynamic property with independent behavior
def CheckExtraProp(TypeName: str, Property: Element, Field: str) -> None:
    if (
        ExtraScaleType(TypeName, Field) != Property.get("type")
        or set(Property.attrib) - {"name", "type", "status"}
        or (Property.text or "").strip()
    ):
        raise ValueError(
            f"FreeCAD editable Scale native {Field} is an additional property"
        )
    if Field == "Label2":
        Label = OnlyEditChild(Property, "String")
        if len(Label) or Label.attrib.keys() != {"value"} or (Label.text or "").strip():
            raise ValueError("FreeCAD editable Scale native label is malformed")


# scale and point use the same implicit element map version as other native parts
def CheckScaleExt(Native: NativeObject) -> None:
    if Native.type_id not in KScaleExtras:
        CheckExtensions(Native)
        return
    Transient = Native.transient_properties
    if Native.extensions or (
        Transient
        and (
            len(Transient) != 1
            or Transient[0].attrib
            != {
                "name": "_ElementMapVersion",
                "type": "App::PropertyString",
                "status": "234881024",
            }
            or len(Transient[0])
        )
    ):
        raise ValueError("FreeCAD editable Scale native extensions changed")


# native modeling defaults cannot supply a second geometric input or alternate solver
def CheckScaleState(Native: NativeObject) -> None:
    CheckScaleExt(Native)
    CheckEmptyProxy(Native)
    Kind = Native.type_id
    if Kind == "Part::Extrusion":
        CheckEditOpts(Native)
        CheckEditMaker(Native)
        CheckEditFrame(Native, "Placement", KTransformIdentity, Optional=True)
    if Kind == "Sketcher::SketchObject":
        CheckSketchOpts(Native)
        CheckExternal(Native)
    if "Role" in Native.properties and EditScalar(
        Native, "Role", "App::PropertyString", "String"
    ):
        raise ValueError("FreeCAD editable Scale native datum role changed")
    if "ShapeMaterial" in Native.properties:
        Material = EditChild(
            Native, "ShapeMaterial", "Materials::PropertyMaterial", "PropertyMaterial"
        )
        CheckMaterial(Material)


# the built in material must remain a plain reference without embedded native data
def CheckMaterial(Material: Element) -> None:
    if (
        len(Material)
        or Material.attrib != {"uuid": "7f9fd73b-50c9-41d8-b7b2-575a030c1eeb"}
        or (Material.text or "").strip()
    ):
        raise ValueError("FreeCAD editable Scale native material changed")
