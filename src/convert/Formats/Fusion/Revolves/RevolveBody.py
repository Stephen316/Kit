from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.BuildRevBody import BuildRevBody
from convert.Formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.Formats.Fusion.Revolves.RevInventory import ReadRevBodies
from convert.Formats.Fusion.Revolves.RevSolidScope import FindRevCreators
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeaturePlaneRev import PlaneRevolve
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.Records.RecordDiagnostic import Diagnostic
from interchange.Records.RecordParameter import Parameter


# reconstruct each supported independent solid after checking the entire native body inventory
def ProjectRevBody(
    BulkData: bytes,
    Spans: tuple[RecordSpan, ...],
    Steps: tuple[FeatureStep, ...],
    Sketches: tuple[Sketch, ...],
    Frames: tuple[SupportPlane, ...],
    Params: tuple[Parameter, ...],
) -> tuple[tuple[DesignBody, ...], BrepModel | None, tuple[Diagnostic, ...]]:
    if not any(
        isinstance(Value.definition, (AngularRevolve, PlaneRevolve)) for Value in Steps
    ):
        return (), None, ()
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    try:
        Creators = FindRevCreators(Steps)
        Links, CollectionId, ComponentId = ReadRevBodies(BulkData, Owners, Creators)
    except ValueError as ErrorInfo:
        return (
            (),
            None,
            (
                Diagnostic(
                    code="fusion.revolve.body_unsupported", message=str(ErrorInfo)
                ),
            ),
        )
    BySketch = {Value.id: Value for Value in Sketches}
    ByFrame = {Value.id: Value for Value in Frames}
    ByParam = {Value.id: Value for Value in Params}
    Bodies: list[DesignBody] = []
    Models: list[BrepModel] = []
    Issues: list[Diagnostic] = []
    for StepValue in Creators:
        try:
            BodyValue, Model = ReadRevModel(
                Owners,
                StepValue,
                ByParam,
                BySketch,
                ByFrame,
                Links,
                CollectionId,
                ComponentId,
            )
        except ValueError as ErrorInfo:
            Issues.append(
                Diagnostic(
                    code="fusion.revolve.body_unsupported",
                    message=str(ErrorInfo),
                    entity_id=StepValue.id,
                    provenance=StepValue.provenance,
                )
            )
            continue
        Bodies.append(BodyValue)
        Models.append(Model)
    Combined = JoinRevModels(tuple(Models)) if Models else None
    return tuple(Bodies), Combined, tuple(Issues)


# each saved solid must resolve its own supported sweep and source frame
def ReadRevModel(
    Owners: dict[int, RecordSpan],
    StepValue: FeatureStep,
    ByParam: dict[str, Parameter],
    BySketch: dict[str, Sketch],
    ByFrame: dict[str, SupportPlane],
    Links: dict[str, tuple[int, int]],
    CollectionId: int,
    ComponentId: int,
) -> tuple[DesignBody, BrepModel]:
    Definition = StepValue.definition
    if not isinstance(Definition, (AngularRevolve, PlaneRevolve)):
        raise ValueError("Missing supported definition for the Fusion result body")
    SketchValue = BySketch.get(StepValue.sketch_id or "")
    FrameValue = (
        None if SketchValue is None else ByFrame.get(SketchValue.support_plane_id)
    )
    if SketchValue is None or FrameValue is None:
        raise ValueError("Missing Fusion Revolve profile sketch frame")
    BodyValue, Model = BuildRevBody(
        Owners,
        StepValue,
        Definition,
        ByParam,
        SketchValue,
        FrameValue,
        Links[StepValue.id],
        CollectionId,
        ComponentId,
    )
    return BodyValue, Model
