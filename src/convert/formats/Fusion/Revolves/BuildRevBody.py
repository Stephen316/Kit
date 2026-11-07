# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

from convert.formats.Fusion.ParamProjection import ParamOrigin
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
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
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Definition: PlaneRevolve | AngularRevolve,
    Interval: tuple[float, float],
    SketchValue: Sketch,
    FrameValue: SupportPlane,
    BodyLink: tuple[int, int],
    CollectionId: int,
    ComponentId: int,
) -> tuple[DesignBody, BrepModel]:
    if FrameValue.attributes.get("fusion.component_object_id") != ComponentId:
        raise ValueError("Fusion Revolve sketch and result body components disagree")
    NativeId, AnchorId = BodyLink
    BodyId = f"fusion-derived-body-{StepValue.id}"
    Model, Volume, Area, Bounds = BuildRevGeom(
        BodyId, StepValue, Definition, Interval, SketchValue, FrameValue.transform
    )
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
