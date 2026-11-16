from dataclasses import replace as ReplaceData

from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumValues import ValueKind
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.geometry.Models.GeometryCurves import CircleGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordParameter import ParameterValue
from tests.Interchange.Fixtures.DocumentFixture import BuildDocument


# a portable standalone sketch gives freecad coverage independent of foreign source payloads
def TypedPart() -> CadDocument:
    Document = BuildDocument()
    Circle = SketchEntity(
        "circle", "circle", CircleGeometry(PlaneVector(0.0, 0.0), 10.0)
    )
    Sketch = ReplaceData(
        Document.sketches[0],
        entities=(Circle,),
        closed_profile_entity_ids=((Circle.id,),),
    )
    Feature = ReplaceData(
        Document.feature_timeline[0],
        definition=ExtrudeFeature(ParameterValue(5.0, ValueKind.LENGTH, "mm")),
    )
    return ReplaceData(Document, sketches=(Sketch,), feature_timeline=(Feature,))
