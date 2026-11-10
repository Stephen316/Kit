# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.adapters.freecad.EditRead.EditGeometry import CheckEditGeom
from convert.adapters.freecad.EditRead.XmlField import EditChild
from convert.adapters.freecad.Native import NativeObject
from interchange.geometry.models.Sketch import Sketch


# geometry and solver lists must still describe the exact selected circle
def CheckEditSketch(Native: NativeObject, Original: Sketch) -> None:
    Geometries = EditChild(
        Native, "Geometry", "Part::PropertyGeometryList", "GeometryList"
    )
    if Geometries.get("count") != str(len(Original.entities)) or len(Geometries) != len(
        Original.entities
    ):
        raise ValueError("FreeCAD editable sketch geometry count changed")
    Selected = Original.closed_profile_entity_ids[0][0]
    for Index, (NodeValue, Entity) in enumerate(zip(Geometries, Original.entities), 1):
        if NodeValue.tag != "Geometry" or NodeValue.get("id") != str(Index):
            raise ValueError("FreeCAD editable sketch geometry order changed")
        CheckEditGeom(NodeValue, Entity, Entity.id == Selected)
    Rules = EditChild(
        Native, "Constraints", "Sketcher::PropertyConstraintList", "ConstraintList"
    )
    if len(Rules) or Rules.get("count") != "0":
        raise ValueError("FreeCAD editable sketch constraints changed")
    if "ExternalGeometry" in Native.properties:
        External = EditChild(
            Native, "ExternalGeometry", "App::PropertyLinkSubList", "LinkSubList"
        )
        if len(External) or External.get("count") != "0":
            raise ValueError("FreeCAD editable sketch external references changed")
