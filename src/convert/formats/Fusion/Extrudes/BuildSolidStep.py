# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from convert.formats.Fusion.Extrudes.BuildExtGeom import BuildExtGeom
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.BuildRevBody import BuildRevBody
from convert.formats.Fusion.Topology.NativeBody import NativeBody
from convert.formats.Fusion.Topology.SolidBodyRecord import MakeSolidRecord
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.DistanceValues import DistExtValues, GetDistValues
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
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
    PlaneValues: DistExtValues | None = None,
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
    if isinstance(Definition, DistanceExtrude):
        Values = GetDistValues(StepValue, Definition, Params)
    elif isinstance(Definition, PlaneExtrude) and PlaneValues is not None:
        Values = PlaneValues
    else:
        raise ValueError("Missing supported Fusion solid definition")
    if FrameValue.attributes.get("fusion.component_object_id") != Member.ComponentId:
        raise ValueError("Fusion Extrude sketch and result body components disagree")
    BodyId = f"fusion-derived-body-{StepValue.id}"
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
