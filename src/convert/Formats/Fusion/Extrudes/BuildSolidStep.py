from convert.Formats.Fusion.Extrudes.BuildExtGeom import BuildExtGeom
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.BuildRevBody import BuildRevBody
from convert.Formats.Fusion.Topology.NativeBody import NativeBody
from convert.Formats.Fusion.Topology.SolidBodyRecord import MakeSolidRecord
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.DistanceValues import DistExtValues, GetDistValues
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeaturePlaneRev import PlaneRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordParameter import Parameter


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
