# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from collections.abc import Mapping
from dataclasses import dataclass as MakeDataClass
from math import hypot as Hypot, isfinite as IsFinite
from typing import cast as CastValue

from convert.adapters.base.WriteValidate import IsObjectMap, IsObjectTuple
from convert.adapters.freecad.EditAxisRev.AxisEndpoints import WorldAxisLine
from convert.adapters.freecad.EditRing.RingEndpoints import ReadRingEnds
from interchange.core.Common import FreezeMapping
from interchange.geometry.models.GeometryCurves import LineGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector

# neutral edits retain the original native axis evidence separately from its live binding
KBodyAxisEdit = "freecad.body_revolve_axis_edit"


# the source entity and its ordered native helper points survive frame and depth changes
@MakeDataClass(frozen=True, slots=True)
class BodyAxisEdit:
    SelectionId: str
    LineId: str
    EndpointIds: tuple[str, str]


# a prior verified edit must still name this exact selection and native sketch line
def ReadAxisEdit(
    Metadata: Mapping[str, object], SelectionId: str
) -> BodyAxisEdit | None:
    if KBodyAxisEdit not in Metadata:
        return None
    RawValue = Metadata[KBodyAxisEdit]
    if (
        not IsObjectMap(RawValue)
        or set(RawValue) != {"selection_id", "line_id", "endpoint_ids"}
        or RawValue["selection_id"] != SelectionId
        or not isinstance(RawValue["line_id"], str)
        or not IsObjectTuple(Endpoints := RawValue["endpoint_ids"])
        or len(Endpoints) != 2
        or any(not isinstance(Value, str) for Value in Endpoints)
    ):
        raise ValueError("FreeCAD edited body axis source binding is malformed")
    return BodyAxisEdit(
        SelectionId,
        RawValue["line_id"],
        CastValue(tuple[str, str], Endpoints),
    )


# only a verified saved edit establishes a separate live line binding for reexport
def StoreAxisEdit(
    Metadata: Mapping[str, object], Binding: BodyAxisEdit
) -> Mapping[str, object]:
    return FreezeMapping(
        {
            **Metadata,
            KBodyAxisEdit: FreezeMapping(
                {
                    "selection_id": Binding.SelectionId,
                    "line_id": Binding.LineId,
                    "endpoint_ids": Binding.EndpointIds,
                }
            ),
        }
    )


# a selected line may only be resolved through its original whole profile entity
def FindAxisEntity(SketchValue: Sketch, LineId: str) -> SketchEntity:
    (Profile,) = SketchValue.closed_profile_entity_ids
    Entities = tuple(Value for Value in SketchValue.entities if Value.id == LineId)
    if LineId not in Profile or len(Entities) != 1:
        raise ValueError("FreeCAD edited body axis source line is missing")
    return Entities[0]


# the original independent edge witness fixes the order of the retained helper points
def BindEditedAxis(
    SketchValue: Sketch,
    Frame: Transform,
    SelectionId: str,
    LineId: str,
    Start: SpaceVector,
    Finish: SpaceVector,
) -> BodyAxisEdit:
    Entity = FindAxisEntity(SketchValue, LineId)
    Geometry = Entity.geometry
    if not isinstance(Geometry, LineGeometry):
        raise ValueError("FreeCAD edited body axis requires a straight source line")
    PointIds = ReadRingEnds(Entity)
    First, Second, _ = WorldAxisLine(Geometry, Frame)
    if (Start, Finish) == (Second, First):
        PointIds = (PointIds[1], PointIds[0])
    elif (Start, Finish) != (First, Second):
        raise ValueError("FreeCAD edited body axis original rim endpoints disagree")
    return BodyAxisEdit(SelectionId, LineId, PointIds)


# the directed raw axis follows the ordered native point identities after edits
def ReadEditedAxis(
    SketchValue: Sketch,
    Frame: Transform,
    Binding: BodyAxisEdit,
) -> tuple[SpaceVector, SpaceVector]:
    Entity = FindAxisEntity(SketchValue, Binding.LineId)
    Geometry = Entity.geometry
    PointIds = ReadRingEnds(Entity)
    if not isinstance(Geometry, LineGeometry):
        raise ValueError("FreeCAD edited body axis requires a straight source line")
    First, Second, _ = WorldAxisLine(Geometry, Frame)
    if Binding.EndpointIds == PointIds:
        return First, Second
    if Binding.EndpointIds == (PointIds[1], PointIds[0]):
        return Second, First
    raise ValueError("FreeCAD edited body axis native endpoints changed identity")


# projected axes use the original straight edge direction computed from world endpoints
def BodyAxisVector(Start: SpaceVector, Finish: SpaceVector) -> SpaceVector:
    Delta = (Finish.x - Start.x, Finish.y - Start.y, Finish.z - Start.z)
    Length = Hypot(*Delta)
    if not IsFinite(Length) or Length <= 1e-9:
        raise ValueError("FreeCAD edited body axis has degenerate world endpoints")
    return SpaceVector(*(Value / Length for Value in Delta))
