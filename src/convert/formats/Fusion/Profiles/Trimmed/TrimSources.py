# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from math import isfinite as IsFinite

from convert.adapters.base.WriteValidate import IsObjectTuple
from interchange.brep.topology.BrepMath import IsFinitePlane
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import CircleGeometry, LineGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity

# local distance precision matches the native geometry checks after unit conversion
KTrimDistance = 1e-8

# angular and affine checks reject coincident cuts without changing their positions
KTrimParameter = 1e-9


# endpoint identities distinguish true authored corners from coordinate coincidences
def GetLinePoints(Entity: SketchEntity) -> tuple[int, int]:
    Points = Entity.attributes.get("fusion.line_native_point_ids")
    if (
        not IsObjectTuple(Points)
        or len(Points) != 2
        or type(Points[0]) is not int
        or type(Points[1]) is not int
        or Points[0] == Points[1]
    ):
        raise ValueError("Missing or ambiguous Fusion trimmed line endpoint identities")
    return Points[0], Points[1]


# native source attributes make the intersection numbering valid in sketch coordinates
def ReadTrimSource(SketchValue: Sketch) -> dict[int, SketchEntity]:
    Sources: dict[int, SketchEntity] = {}
    EntityIds: set[str] = set()
    for Entity in SketchValue.entities:
        if Entity.kind == GeometryKind.KPoint:
            continue
        if len(Sources) == 8:
            raise ValueError(
                "Fusion trimmed profile source exceeds the captured curve count"
            )
        TagValue = Entity.attributes.get("fusion.entity_tag")
        if (
            type(TagValue) is not int
            or TagValue in Sources
            or Entity.id in EntityIds
            or Entity.construction
            or Entity.attributes.get("fusion.entity_genesis") != 2
        ):
            raise ValueError("Unsupported or ambiguous Fusion trimmed profile source")
        Geometry = Entity.geometry
        if isinstance(Geometry, LineGeometry):
            _ = GetLinePoints(Entity)
            if not (
                IsFinitePlane(Geometry.start)
                and IsFinitePlane(Geometry.end)
                and Geometry.start != Geometry.end
            ):
                raise ValueError("Invalid Fusion trimmed source line")
        elif isinstance(Geometry, CircleGeometry):
            if (
                not IsFinitePlane(Geometry.center)
                or not IsFinite(Geometry.radius)
                or Geometry.radius <= KTrimDistance
                or Entity.attributes.get("fusion.circle_native_normal")
                != (0.0, 0.0, 1.0)
                or Entity.attributes.get("fusion.circle_native_reference_axis")
                != (1.0, 0.0, 0.0)
            ):
                raise ValueError("Unsupported Fusion trimmed source circle frame")
        else:
            raise ValueError("Unsupported Fusion trimmed profile source curve")
        Sources[TagValue] = Entity
        EntityIds.add(Entity.id)
    return Sources
