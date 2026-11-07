# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace
from math import isclose as IsClose, tau as FullTurn

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.BodyMeridian import ReadMeridian
from convert.formats.Fusion.Revolves.RevProfile import ReadRevProfile
from convert.formats.Fusion.Topology.BodyCollection import ReadSingleBody
from convert.formats.Fusion.Topology.ResultBody import FindResultBody
from convert.geometry.Revolve.PolygonSweep import BuildPolySweep
from convert.geometry.Revolve.SweepMetrics import MeasureSweep
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordTopology import TopologyCounts


# source operands generate new topology while native records identify the result body
def BuildRevBody(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Definition: PlaneRevolve | AngularRevolve,
    Interval: tuple[float, float],
    SketchValue: Sketch,
    FrameValue: SupportPlane,
) -> tuple[DesignBody, BrepModel]:
    if IsClose(Interval[1] - Interval[0], FullTurn, rel_tol=0.0, abs_tol=1e-10):
        raise ValueError(
            "Fusion full turn Revolve solid requires a periodic topology path"
        )
    Origin = StepValue.provenance
    ComponentId = FrameValue.attributes.get("fusion.component_object_id")
    if Origin is None or not isinstance(ComponentId, int):
        raise ValueError("Missing Fusion Revolve body owner or component")
    NativeId, AnchorId = FindResultBody(BulkData, Owners, int(Origin.native_id))
    CollectionId = ReadSingleBody(BulkData, Owners, NativeId, ComponentId)
    Profile = ReadRevProfile(StepValue, SketchValue)
    if not isinstance(Profile, tuple):
        raise ValueError("Fusion Revolve solid currently requires a line profile")
    Meridian, Radial = ReadMeridian(
        FrameValue.transform,
        Profile,
        Definition.AxisOrigin,
        Definition.AxisDirection,
    )
    BodyId = f"fusion-derived-body-{StepValue.id}"
    SweepArgs = (
        Meridian,
        Definition.AxisOrigin,
        Definition.AxisDirection,
        Radial,
        *Interval,
    )
    Model = BuildPolySweep(BodyId, *SweepArgs)
    Errors = Model.GetErrors(frozenset((BodyId,)))
    if Errors:
        raise ValueError("; ".join(Errors))
    Volume, Area, Bounds = MeasureSweep(*SweepArgs)
    NativeOrigin = ParamOrigin(Owners[NativeId])
    Body = DesignBody(
        id=BodyId,
        name=StepValue.name or "Revolve result",
        final_feature_id=StepValue.id,
        topology=TopologyCounts(
            solid_count=len(Model.regions),
            shell_count=len(Model.shells),
            face_count=len(Model.faces),
            edge_count=len(Model.edges),
            vertex_count=len(Model.vertices),
            volume=Volume,
            surface_area=Area,
            bounding_box=Bounds,
            valid=True,
        ),
        provenance=Replace(
            NativeOrigin,
            spans=NativeOrigin.spans
            + ParamOrigin(Owners[AnchorId]).spans
            + ParamOrigin(Owners[CollectionId]).spans,
        ),
        attributes=FreezeMapping(
            {
                "fusion.geometry_source": "source_profile_revolve",
                "fusion.native_body_anchor_id": AnchorId,
                "fusion.native_body_collection_id": CollectionId,
            }
        ),
    )
    return Body, Model
