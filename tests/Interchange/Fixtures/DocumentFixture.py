from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumDocument import Capability
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureBody import DesignBody
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry
from interchange.geometry.Models.Sketch import Sketch, SketchEntity
from interchange.geometry.Models.SupportPlane import SupportPlane
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorPlane import PlaneVector
from interchange.Records.RecordConfig import Configuration
from interchange.Records.RecordSource import CadSource


# the canonical document fixture keeps domain tests independent from test modules
def BuildDocument() -> CadDocument:
    PlaneValue = SupportPlane("plane:xy", "XY", Transform())
    EntityValue = SketchEntity(
        "sketch:1:line:1",
        "line",
        LineGeometry(PlaneVector(0.0, 0.0), PlaneVector(10.0, 0.0)),
    )
    SketchValue = Sketch("sketch:1", "Sketch1", PlaneValue.EntityId, (EntityValue,))
    FeatureValue = FeatureStep(
        "feature:1", "Boss1", FeatureKind.KExtrusion, 0, sketch_id=SketchValue.id
    )
    BodyValue = DesignBody("body:1", "Body", FeatureValue.EntityId)
    return CadDocument(
        source=CadSource("test", "memory", "0" * 64),
        configurations=(Configuration("config:default", "Default", True),),
        parameters=(),
        support_planes=(PlaneValue,),
        sketches=(SketchValue,),
        selections=(),
        feature_timeline=(FeatureValue,),
        bodies=(BodyValue,),
        capabilities=frozenset(
            {Capability.KParamHistory, Capability.KEditableSketches}
        ),
    )
