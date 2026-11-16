from dataclasses import replace as ReplaceData

from convert.adapters.Fusion.Authoring.MakeFusionDoc import MakeFusionDoc
from convert.Formats.Fusion.DocumentCodec.Model.DocumentSpec import DocumentSpec
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureKinds import CombineFeature
from tests.Interchange.Fixtures.DocumentFixture import BuildDocument

# negative histories need explicit kind variants that remain valid neutral documents
KBadKinds = {
    "GenericStep": FeatureKind.KExtrusion,
    "EmptyDefinition": FeatureKind.KExtrusion,
    "NativeKind": FeatureKind.KNative,
    "NativeDefined": FeatureKind.KNative,
    "Imported": FeatureKind.KImported,
    "ImportedDefined": FeatureKind.KImported,
    "UnknownKind": "fixture.unknown",
    "UnknownDefined": "fixture.unknown",
    "BareReference": FeatureKind.KReference,
    "BodyReference": FeatureKind.KReference,
}


# incomplete history coverage must reach cli qualification rather than fail during fixture construction
def BuildBadStep(RecordKind: str) -> CadDocument:
    if RecordKind == "GenericStep":
        return BuildDocument()
    Document = MakeFusionDoc(
        DocumentSpec(
            "Incomplete feature",
            "height",
            20.0,
            ProfileKind="cuboid",
            ConstrainRectangle=True,
        )
    )
    Feature = Document.feature_timeline[-1]
    Feature = ReplaceData(
        Feature,
        kind=KBadKinds[RecordKind],
        definition=(
            CombineFeature()
            if RecordKind in ("UnknownDefined", "NativeDefined", "ImportedDefined")
            else None
        ),
        sketch_id=None if RecordKind == "BareReference" else Feature.sketch_id,
    )
    return ReplaceData(
        Document,
        feature_timeline=(*Document.feature_timeline[:-1], Feature),
        metadata={},
    )
