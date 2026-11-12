from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.Revolves.AngleRevValues import ReadAngleSpan
from convert.formats.Fusion.Revolves.BuildRevGeom import BuildRevGeom
from convert.formats.Fusion.Topology.SolidBodyRecord import MakeSolidRecord
from interchange.brep.topology.BrepModel import BrepModel
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBody import DesignBody
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.records.RecordParameter import Parameter


# source operands generate new topology while native records identify the result body
def BuildRevBody(
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    Definition: PlaneRevolve | AngularRevolve,
    Params: dict[str, Parameter],
    SketchValue: Sketch,
    FrameValue: SupportPlane,
    BodyLink: tuple[int, int],
    CollectionId: int,
    ComponentId: int,
) -> tuple[DesignBody, BrepModel]:
    if FrameValue.attributes.get("fusion.component_object_id") != ComponentId:
        raise ValueError("Fusion Revolve sketch and result body components disagree")
    Interval = (
        (Definition.StartRadians, Definition.EndRadians)
        if isinstance(Definition, PlaneRevolve)
        else ReadAngleSpan(Definition, Params)
    )
    BodyId = f"fusion-derived-body-{StepValue.id}"
    return MakeSolidRecord(
        BodyId,
        "Revolve result",
        StepValue,
        BuildRevGeom(
            BodyId, StepValue, Definition, Interval, SketchValue, FrameValue.transform
        ),
        Owners,
        BodyLink,
        CollectionId,
        "source_profile_revolve",
    )
