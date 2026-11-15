from convert.Commands.CanGenerate import CanGenerate
from convert.Commands.CheckStep import CheckStep, KFeatureError
from convert.Commands.ProfileInputs import ProfileInputs
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind


# local geometry needs a complete active generator history before conversion can proceed
def CheckFeatures(Document: CadDocument) -> None:
    Generators = set[str]()
    ActiveFeatures = set[str]()
    SketchInputs: dict[str, set[str]] = {}
    Sketches = {Sketch.id: Sketch for Sketch in Document.sketches}
    Profiles = ProfileInputs(Document.sketches)
    Frames = {Frame.id: Frame for Frame in Document.support_planes}
    Parameters = {Param.id: Param for Param in Document.parameters}
    Selections = {Selection.id: Selection for Selection in Document.selections}
    IdentitySets = {"sketches": set(Sketches), "support_planes": set(Frames)}
    SuppressedFeatures = {
        FeatureId
        for Configuration in Document.configurations
        for FeatureId in Configuration.suppressed_feature_ids
    }

    # feature dependencies need chronological processing to establish active generators
    for Feature in sorted(Document.feature_timeline, key=lambda Value: Value.order):
        CheckStep(Feature, IdentitySets, Selections, Parameters, Frames, Sketches)
        if (
            Feature.suppressed
            or Feature.id in SuppressedFeatures
            or any(State.suppressed for State in Feature.configuration_states)
            or any(
                InputId not in ActiveFeatures for InputId in Feature.input_feature_ids
            )
        ):
            continue
        ActiveFeatures.add(Feature.id)
        if Feature.kind == FeatureKind.KReference:
            if (
                Feature.sketch_id is not None
                and Feature.sketch_id in Sketches
                and Feature.definition is None
                and not Sketches[Feature.sketch_id].suppressed
            ):
                SketchInputs.setdefault(Feature.sketch_id, set()).add(Feature.id)
            continue
        if not CanGenerate(Feature, Profiles, SketchInputs, Generators):
            raise ValueError(KFeatureError)
        Generators.add(Feature.id)
    if (
        (Document.feature_timeline and not ActiveFeatures)
        or Document.meshes
        or any(Sketch.id not in SketchInputs for Sketch in Document.sketches)
        or any(
            BodyValue.final_feature_id not in Generators
            for BodyValue in Document.bodies
        )
    ):
        raise ValueError(KFeatureError)
    BodyIds = {BodyValue.id for BodyValue in Document.bodies}
    if Document.brep is not None and (
        not Document.brep.bodies
        or any(
            BodyValue.design_body_id not in BodyIds
            for BodyValue in Document.brep.bodies
        )
    ):
        raise ValueError(KFeatureError)
