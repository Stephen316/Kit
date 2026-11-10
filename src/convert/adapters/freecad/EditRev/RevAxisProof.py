# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from convert.formats.Fusion.DesignZip import KDesignPrefix
from convert.formats.Fusion.Revolves.OriginAxis import KAxisGuid, KOriginGuid
from convert.formats.Fusion.SelectionProxy import KSelectProxy
from convert.formats.Fusion.SelectionRef import KSelectDesc, KSelectLeaf
from convert.geometry.Revolve.SweepVector import DotVector, OffsetVector
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Transform import Transform


# source axis ownership remains exact only for the captured component origin axes
def CheckRevAxis(
    FeatureValue: FeatureStep,
    Definition: AngularRevolve,
    AxisPick: Selection,
    FrameValue: Transform,
) -> None:
    Attrs = FeatureValue.attributes
    NativeId = Attrs.get("fusion.revolve.axis_selection_id")
    AxisId = Attrs.get("fusion.revolve.axis_object_id")
    Origin = AxisPick.provenance
    AxisName = AxisPick.query.get("axis")
    if (
        type(NativeId) is not int
        or NativeId <= 0
        or type(AxisId) is not int
        or AxisId <= 0
        or AxisPick.id != f"fusion-selection-{NativeId}-axis"
        or AxisPick.id != Definition.AxisSelectionId
        or FeatureValue.selection_ids != (AxisPick.id,)
        or AxisPick.path
        or AxisPick.query != {"kind": "component_origin_axis", "axis": AxisName}
        or AxisName not in ("X", "Y", "Z")
        or Origin is None
        or Origin.adapter != "fusion.f3d"
        or Origin.native_id != str(NativeId)
    ):
        raise ValueError("FreeCAD editable Revolve has no exact origin axis selection")
    Kinds = {
        SpanValue.record_kind
        for SpanValue in Origin.spans
        if SpanValue.stream == KDesignPrefix + "BulkStream.dat"
        and SpanValue.offset >= 0
        and SpanValue.length > 0
    }
    AxisValue = Definition.AxisDirection
    Start = Definition.AxisOrigin
    Offset = OffsetVector(Start, FrameValue.origin, -1.0)
    if (
        not {KSelectProxy, KSelectDesc, KSelectLeaf, KAxisGuid, KOriginGuid} <= Kinds
        or any(abs(Value) > 1e-8 for Value in (Start.x, Start.y, Start.z))
        or any(
            abs(abs(Value) - float(NameValue == AxisName)) > 1e-9
            for NameValue, Value in zip(
                "XYZ", (AxisValue.x, AxisValue.y, AxisValue.z), strict=True
            )
        )
        or abs(DotVector(FrameValue.z_axis, AxisValue)) > 1e-9
        or abs(DotVector(FrameValue.z_axis, Offset)) > 1e-8
    ):
        raise ValueError("FreeCAD editable Revolve axis evidence or geometry disagrees")
