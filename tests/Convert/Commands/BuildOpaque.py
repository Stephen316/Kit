from dataclasses import replace as ReplaceData

from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.Features.FeatureKinds import NativeFeature
from interchange.geometry.Models.GeometryCurves import NativeGeometry
from tests.Interchange.Fixtures.AssemblyFixture import BuildAssembly
from tests.Interchange.Fixtures.DocumentFixture import BuildDocument


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
