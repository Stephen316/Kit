from __future__ import annotations

from typing import TYPE_CHECKING as TypeChecking, Mapping
from interchange import ParameterValue as ParamValue, RevolutionFeature, ValueKind
from convert.adapters.solidworks.core.AxisSketchId import AxisSketchId
from convert.adapters.solidworks.core.SketchIdentity import AxisSourceId, MarkerId

if TypeChecking:
    from convert.adapters.solidworks.core.Native import NativeOperation, NativeSketch


def BuildRevolve(
    Operation: NativeOperation | None, Sketches: Mapping[int, NativeSketch]
) -> RevolutionFeature | None:
    if (
        Operation is None
        or Operation.kind not in {"revolve_join", "revolve_cut"}
        or Operation.angle_degrees is None
    ):
        return None
    AxisId = AxisSketchId(
        Operation.profile_id, Operation.axis_source_kind, Operation.axis_source_id
    )
    AxisSketch = Sketches.get(AxisId) if AxisId is not None else None
    if (
        AxisSketch is not None
        and Operation.axis_marker_offset is not None
        and any(
            Marker.offset == Operation.axis_marker_offset
            for Marker in AxisSketch.markers
        )
    ):
        Reference = MarkerId(AxisSketch.object_id, Operation.axis_marker_offset)
    elif (
        Operation.axis_source_kind is not None and Operation.axis_source_id is not None
    ):
        Reference = AxisSourceId(Operation.axis_source_kind, Operation.axis_source_id)
    else:
        return None
    return RevolutionFeature(
        angle=ParamValue(Operation.angle_degrees, ValueKind.ANGLE, "deg"),
        axis_entity_id=Reference,
        reversed=Operation.kind == "revolve_cut",
    )
