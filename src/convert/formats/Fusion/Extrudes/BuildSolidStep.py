# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.Extrudes.BuildExtGeom import BuildExtGeom
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.BuildRevBody import BuildRevBody
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from convert.formats.Fusion.Topology.SolidBodyRecord import MakeSolidRecord
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# each geometry builder consumes the same verified component and body ownership evidence
def BuildSolidStep(
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    SketchValue: Sketch,
    FrameValue: SupportPlane,
    Params: dict[str, Parameter],
    Member: NativeBody,
    AnchorId: int,
) -> tuple[DesignBody, BrepModel]:
    Definition = StepValue.definition
    BodyLink = (Member.ObjectId, AnchorId)
    if isinstance(Definition, (AngularRevolve, PlaneRevolve)):
        return BuildRevBody(
            Owners,
            StepValue,
            Definition,
            Params,
            SketchValue,
            FrameValue,
            BodyLink,
            Member.CollectionId,
            Member.ComponentId,
        )
    if not isinstance(Definition, DistanceExtrude):
        raise ValueError("Missing supported Fusion solid definition")
    if FrameValue.attributes.get("fusion.component_object_id") != Member.ComponentId:
        raise ValueError("Fusion Extrude sketch and result body components disagree")
    BodyId = f"fusion-derived-body-{StepValue.id}"
    Values = GetDistValues(StepValue, Definition, Params)
    Geometry = BuildExtGeom(
        BodyId, StepValue, Definition, Values, SketchValue, FrameValue.transform
    )
    return MakeSolidRecord(
        BodyId,
        "Extrude result",
        StepValue,
        Geometry,
        Owners,
        BodyLink,
        Member.CollectionId,
        "source_profile_extrude",
    )
