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
from interchange.brep.topology.BrepModel import BrepModel
from interchange.core.Common import FreezeMapping
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.BoundingBox import BoundingBox
from interchange.records.RecordTopology import TopologyCounts


# exact topology and native ownership share one result record across independent solid builders
def MakeSolidRecord(
    BodyId: str,
    BodyName: str,
    StepValue: FeatureStep,
    Geometry: tuple[BrepModel, float, float, BoundingBox],
    Owners: dict[int, RecordSpan],
    BodyLink: tuple[int, int],
    CollectionId: int,
    SourceKind: str,
) -> tuple[DesignBody, BrepModel]:
    Model, Volume, Area, Bounds = Geometry
    NativeId, AnchorId = BodyLink
    Origin = ParamOrigin(Owners[NativeId])
    BodyValue = DesignBody(
        id=BodyId,
        name=StepValue.name or BodyName,
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
            Origin,
            spans=Origin.spans
            + ParamOrigin(Owners[AnchorId]).spans
            + ParamOrigin(Owners[CollectionId]).spans,
        ),
        attributes=FreezeMapping(
            {
                "fusion.geometry_source": SourceKind,
                "fusion.native_body_anchor_id": AnchorId,
                "fusion.native_body_collection_id": CollectionId,
            }
        ),
    )
    return BodyValue, Model
