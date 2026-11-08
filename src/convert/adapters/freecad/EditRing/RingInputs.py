# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from convert.adapters.freecad.EditRing.RingEndpoints import CheckRingEnds, ReadRingEnds
from convert.geometry.Extrude.Polygon.PrismRing import MeasureRing, ReadPrismRing
from interchange.brep.topology.BrepMath import IsFinitePlane
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import LineGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity


# explicit source entity identities keep retained helper points distinguishable
def ReadRingEnts(
    SketchValue: Sketch,
) -> tuple[tuple[str, ...], dict[str, SketchEntity]]:
    Origin = SketchValue.provenance
    Profiles = SketchValue.closed_profile_entity_ids
    if (
        SketchValue.suppressed
        or SketchValue.constraints
        or SketchValue.parameter_ids
        or SketchValue.attributes.get("freecad")
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or SketchValue.id != f"fusion-sketch-{Origin.native_id}"
        or len(Profiles) != 1
        or not 3 <= len(Profiles[0]) <= 64
        or len(set(Profiles[0])) != len(Profiles[0])
    ):
        raise ValueError(
            "FreeCAD editable ring requires one whole native sketch profile"
        )
    Entities = {Value.id: Value for Value in SketchValue.entities}
    if (
        len(Entities) != len(SketchValue.entities)
        or not set(Profiles[0]) <= Entities.keys()
    ):
        raise ValueError(
            "FreeCAD editable ring profile entities are ambiguous or missing"
        )
    return Profiles[0], Entities


# whole line geometry and exact point records must corroborate the same simple ring
def ReadRingInput(
    SketchValue: Sketch,
) -> tuple[tuple[LineGeometry, ...], frozenset[str]]:
    Members, Entities = ReadRingEnts(SketchValue)
    MemberSet = set(Members)
    Lines: dict[str, LineGeometry] = {}
    Points: dict[str, PointGeometry] = {}
    for Identity, Entity in Entities.items():
        Origin = Entity.provenance
        Geometry = Entity.geometry
        if (
            Entity.fixed
            or Origin is None
            or Origin.adapter != "fusion.f3d"
            or Identity != f"fusion-sketch-entity-{Origin.native_id}"
        ):
            raise ValueError("FreeCAD editable ring has an unproven source entity")
        if Identity in MemberSet:
            if (
                Entity.kind != GeometryKind.KLine
                or not isinstance(Geometry, LineGeometry)
                or Entity.construction
            ):
                raise ValueError(
                    "FreeCAD editable ring requires whole nonconstruction lines"
                )
            Lines[Identity] = Geometry
        elif (
            Entity.kind == GeometryKind.KPoint
            and isinstance(Geometry, PointGeometry)
            and IsFinitePlane(Geometry.point)
        ):
            Points[Identity] = Geometry
        else:
            raise ValueError("FreeCAD editable ring has unsupported helper geometry")
    Endpoints = tuple(ReadRingEnds(Entities[Identity]) for Identity in Members)
    PointIds = CheckRingEnds(Endpoints)
    if not PointIds <= Points.keys():
        raise ValueError("FreeCAD editable ring native endpoint geometry is missing")
    Profile = tuple(Lines[Identity] for Identity in Members)
    for Geometry, (Start, EndId) in zip(Profile, Endpoints, strict=True):
        if Geometry.start != Points[Start].point or Geometry.end != Points[EndId].point:
            raise ValueError(
                "FreeCAD editable ring line and native point geometry disagree"
            )
    MeasureRing(ReadPrismRing(Profile))
    return Profile, PointIds
