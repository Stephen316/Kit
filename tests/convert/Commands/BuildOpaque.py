from dataclasses import replace as ReplaceData

from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumGeometry import GeometryKind
from interchange.features.FeatureKinds import NativeFeature
from interchange.geometry.models.GeometryCurves import NativeGeometry
from tests.interchange.fixtures.AssemblyFixture import BuildAssembly
from tests.interchange.fixtures.DocumentFixture import BuildDocument


# opaque feature geometry and research markers must remain inspectable without qualifying for conversion
def BuildOpaque(RecordKind: str, IsNested: bool) -> CadDocument:
    Document = BuildDocument()
    if RecordKind == "UnqualifiedResearch":
        Document = ReplaceData(
            Document,
            metadata=FreezeMapping({"kit.research_read_status": "unqualified"}),
        )
    elif RecordKind == "NativeFeature":
        Document = ReplaceData(
            Document,
            feature_timeline=(
                ReplaceData(
                    Document.FeatureTimeline[0],
                    kind=FeatureKind.KNative,
                    definition=NativeFeature("fixture.native", "unknown"),
                ),
            ),
        )
    else:
        Sketch = Document.Sketches[0]
        Entity = ReplaceData(
            Sketch.Entities[0],
            kind=GeometryKind.KNative,
            geometry=NativeGeometry("fixture.native", "unknown"),
        )
        Document = ReplaceData(
            Document, sketches=(ReplaceData(Sketch, entities=(Entity,)),)
        )
    if not IsNested:
        return Document
    Assembly = BuildAssembly()
    assert Assembly.assembly is not None
    Nested = ReplaceData(Assembly.assembly.documents[0], document=Document)
    return ReplaceData(
        Assembly, assembly=ReplaceData(Assembly.assembly, documents=(Nested,))
    )
