# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.Sketches.SketchPrimitive import KSketchKinds
from interchange.brep.topology.BrepMath import IsFinitePlane
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import SketchEntity
from interchange.geometry.models.VectorPlane import PlaneVector


# each input primitive must be an original native record with its own identity
def CheckAxisEntity(Entity: SketchEntity, KindValue: GeometryKind) -> None:
    Origin = Entity.provenance
    if (
        Entity.fixed
        or Entity.kind != KindValue
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Entity.id != f"fusion-sketch-entity-{Origin.native_id}"
        or int(Origin.native_id) <= 0
        or len(Origin.spans) != 1
        or KSketchKinds.get(Origin.spans[0].record_kind) != KindValue
        or Origin.spans[0].stream != KDesignPrefix + "BulkStream.dat"
        or Origin.spans[0].offset < 0
        or Origin.spans[0].length <= 0
    ):
        raise ValueError(
            "FreeCAD editable sketch axis primitive provenance is unresolved"
        )


# construction state distinguishes the selected axis from its owning endpoint points
def ReadAxisPoint(Entity: SketchEntity) -> PlaneVector:
    CheckAxisEntity(Entity, GeometryKind.KPoint)
    Geometry = Entity.geometry
    if (
        Entity.construction
        or not isinstance(Geometry, PointGeometry)
        or not IsFinitePlane(Geometry.point)
    ):
        raise ValueError("FreeCAD editable sketch axis helper point is unsupported")
    return Geometry.point


# only complete native line primitives can drive the axis or source profile
def ReadAxisGeom(Entity: SketchEntity, Construction: bool) -> LineGeometry:
    CheckAxisEntity(Entity, GeometryKind.KLine)
    Geometry = Entity.geometry
    if (
        Entity.construction != Construction
        or not isinstance(Geometry, LineGeometry)
        or not IsFinitePlane(Geometry.start)
        or not IsFinitePlane(Geometry.end)
        or Geometry.start == Geometry.end
    ):
        raise ValueError("FreeCAD editable sketch axis line geometry is unsupported")
    return Geometry
