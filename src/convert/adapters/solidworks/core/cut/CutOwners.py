from convert.adapters.solidworks.container.ArchiveCheck import RequireArch
from convert.adapters.solidworks.container.Format import PART_FORMAT_ID as KPartFormatId
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumUnits import UnitSystem
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Sketch import Sketch


# the reached profile can change only its uniquely owned neutral sketch and feature step
def FindCutOwner(Document: CadDocument, ProfileId: int) -> tuple[Sketch, FeatureStep]:
    RequireArch(
        Document.source.format_id, KPartFormatId, "derived solidworks part source"
    )
    RequireArch(Document.units, UnitSystem.KMillimeter, "neutral local sketch units")
    SketchId = f"sldprt:sketch:{ProfileId}"
    FeatureId = f"sldprt:feature:{ProfileId}"
    Sketches = [Value for Value in Document.sketches if Value.id == SketchId]
    Features = [Value for Value in Document.feature_timeline if Value.id == FeatureId]
    RequireArch((len(Sketches), len(Features)), (1, 1), "unique cut profile owners")
    (SketchValue,), (Feature,) = Sketches, Features
    RequireArch(
        (
            SketchValue.attributes.get("native_object_id"),
            Feature.kind,
            Feature.sketch_id,
            SketchValue.suppressed,
            Feature.suppressed,
        ),
        (ProfileId, FeatureKind.KReference, SketchId, False, False),
        "active cut profile owns this sketch",
    )
    return SketchValue, Feature
