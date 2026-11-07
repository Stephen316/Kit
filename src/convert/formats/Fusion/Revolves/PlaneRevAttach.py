# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.PlaneCollection import ReadPlaneComp
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.OriginAxis import ReadOriginAxis
from convert.formats.Fusion.Revolves.PlaneRevInputs import ProfileLines, TargetPlanes
from convert.formats.Fusion.Revolves.PlaneSweep import DerivePlaneSpan
from convert.formats.Fusion.SelectionRef import ReadEntityRef
from interchange.core.Common import FreezeMapping
from interchange.enums.EnumFeatures import BooleanOp
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane


# source planes and the occupied sketch meridian determine the bounded sweep
def AttachPlaneRev(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Picks: tuple[Selection, ...],
    Frames: dict[str, SupportPlane],
    SketchValue: Sketch | None,
) -> tuple[FeatureStep, Selection]:
    Origin = StepValue.provenance
    Attrs = StepValue.attributes
    if (
        Origin is None
        or SketchValue is None
        or Attrs.get("fusion.revolve.operation") != "new_body"
        or Attrs.get("fusion.revolve.solid") is not True
        or Attrs.get("fusion.revolve.project_axis") is not False
    ):
        raise ValueError("Fusion plane Revolve requires an unprojected solid new body")
    SketchFrame = Frames.get(SketchValue.support_plane_id)
    ComponentId = (
        None
        if SketchFrame is None
        else SketchFrame.attributes.get("fusion.component_object_id")
    )
    AxisId = Attrs.get("fusion.revolve.axis_object_id")
    SelectId = Attrs.get("fusion.revolve.axis_selection_id")
    if SketchFrame is None or not all(
        isinstance(Identity, int) for Identity in (ComponentId, AxisId, SelectId)
    ):
        raise ValueError("Missing Fusion plane Revolve sketch component or origin axis")
    AxisName, AxisOrigin, StoredAxis, ContainerId = ReadOriginAxis(
        BulkData, Owners, AxisId, ComponentId
    )
    Targets = TargetPlanes(StepValue, Picks, Frames)
    Collections = []
    for _, PlaneValue in Targets:
        PlaneComponent, CollectionId = ReadPlaneComp(BulkData, Owners, PlaneValue)
        if PlaneComponent != ComponentId:
            raise ValueError("Fusion plane Revolve target component disagrees")
        Collections.append(CollectionId)
    EffectiveAxis, Start, EndValue = DerivePlaneSpan(
        SketchFrame.transform,
        ProfileLines(StepValue, SketchValue),
        AxisOrigin,
        StoredAxis,
        tuple(PlaneValue.transform for _, PlaneValue in Targets),
    )
    Descriptor, Terminal, _ = ReadEntityRef(
        BulkData, Owners, SelectId, int(Origin.native_id)
    )
    SelectOrigin = ParamOrigin(Owners[SelectId])
    AxisSpans = SelectOrigin.spans + tuple(
        SpanValue
        for Identity in (Descriptor, Terminal, AxisId, ContainerId)
        for SpanValue in ParamOrigin(Owners[Identity]).spans
    )
    AxisPick = Selection(
        id=f"fusion-selection-{SelectId}-axis",
        name="axis",
        path=(),
        query=FreezeMapping({"kind": "component_origin_axis", "axis": AxisName}),
        provenance=Replace(SelectOrigin, spans=AxisSpans),
    )
    Evidence = tuple(
        SpanValue
        for Identity in dict.fromkeys((ContainerId, *Collections))
        for SpanValue in ParamOrigin(Owners[Identity]).spans
    )
    Definition = PlaneRevolve(
        AxisSelectionId=AxisPick.id,
        PlaneSelectionIds=tuple(PickValue.id for PickValue, _ in Targets),
        AxisOrigin=AxisOrigin,
        AxisDirection=EffectiveAxis,
        StartRadians=Start,
        EndRadians=EndValue,
    )
    return (
        Replace(
            StepValue,
            definition=Definition,
            operation=BooleanOp.KCreate,
            selection_ids=(AxisPick.id,) + StepValue.selection_ids,
            provenance=Replace(Origin, spans=Origin.spans + Evidence),
        ),
        AxisPick,
    )
