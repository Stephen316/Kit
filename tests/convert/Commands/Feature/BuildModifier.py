from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureStep import FeatureStep
from tests.convert.Commands.Feature.AddCreator import AddCreator
from tests.convert.Commands.Feature.ModifierCases import KModifierSpecs


# modifier qualification needs valid neutral documents with deliberately insufficient generative evidence
def BuildModifier(RecordKind: str) -> CadDocument:
    Document = MakeFusionDoc(
        DocumentSpec(
            "Modifier prerequisites",
            "height",
            20.0,
            ProfileKind="cuboid",
            ConstrainRectangle=True,
        )
    )
    if RecordKind in (
        "CombineInactive",
        "CombineBadOperation",
        "CombineValid",
        "CombineCut",
    ):
        Document = AddCreator(Document)
    KindValue, Definition, Inputs = KModifierSpecs[RecordKind]
    Feature = FeatureStep(
        "modifier",
        RecordKind,
        KindValue,
        max(StepValue.order for StepValue in Document.feature_timeline) + 1,
        Inputs,
        definition=Definition,
    )
    return ReplaceData(
        Document,
        metadata={},
        feature_timeline=tuple(
            (
                ReplaceData(StepValue, suppressed=True)
                if RecordKind == "CombineInactive" and StepValue.id == "other"
                else StepValue
            )
            for StepValue in (*Document.feature_timeline, Feature)
        ),
        bodies=tuple(
            ReplaceData(BodyValue, final_feature_id=Feature.id)
            for BodyValue in Document.bodies
        ),
    )
