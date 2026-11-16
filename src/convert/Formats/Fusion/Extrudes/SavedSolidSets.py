from convert.Formats.Fusion.Extrudes.BuildSolidStep import BuildSolidStep
from convert.Formats.Fusion.Extrudes.ExtBodyLinks import LinkSolidBodies
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from convert.Formats.Fusion.Topology.NativeBody import NativeBody
from interchange.brep.Topology.BrepModel import BrepModel
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeatureStep import FeatureStep
from interchange.Features.PlaneExtValues import GetPlaneExt


# component local geometry is grouped before assembly occurrences can apply placement
def BuildSolidSets(
    Document: CadDocument,
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Creators: tuple[FeatureStep, ...],
    Members: tuple[NativeBody, ...],
) -> dict[int, tuple[tuple[DesignBody, ...], BrepModel]]:
    Sketches = {SketchValue.id: SketchValue for SketchValue in Document.sketches}
    Frames = {FrameValue.id: FrameValue for FrameValue in Document.support_planes}
    Params = {Param.id: Param for Param in Document.parameters}
    Selections = {Selection.id: Selection for Selection in Document.selections}
    Bodies: dict[int, list[DesignBody]] = {}
    Models: dict[int, list[BrepModel]] = {}
    Links = LinkSolidBodies(BulkData, Owners, Creators, Members)
    for StepValue in Creators:
        SketchValue = Sketches.get(StepValue.sketch_id or "")
        FrameValue = (
            None if SketchValue is None else Frames.get(SketchValue.support_plane_id)
        )
        if SketchValue is None or FrameValue is None:
            raise ValueError("Missing Fusion solid profile sketch frame")
        Member, AnchorId = Links[StepValue.id]
        Definition = StepValue.definition
        PlaneValues = (
            GetPlaneExt(StepValue, Definition, Params, Selections, Frames, Sketches)
            if isinstance(Definition, PlaneExtrude)
            else None
        )
        BodyValue, Model = BuildSolidStep(
            Owners,
            StepValue,
            SketchValue,
            FrameValue,
            Params,
            Member,
            AnchorId,
            PlaneValues,
        )
        Bodies.setdefault(Member.ComponentId, []).append(BodyValue)
        Models.setdefault(Member.ComponentId, []).append(Model)
    return {
        ComponentId: (tuple(BodyList), JoinRevModels(tuple(Models[ComponentId])))
        for ComponentId, BodyList in Bodies.items()
    }
