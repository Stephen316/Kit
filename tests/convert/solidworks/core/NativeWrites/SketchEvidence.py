from dataclasses import replace as ReplaceData

from convert import open_document as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumGeometry import GeometryKind
from interchange.geometry.models.GeometryCurves import NativeGeometry
from tests.convert.api.ApiTestPaths import KSamplePath
from tests.convert.api.Fusion.AdapterCases import AdapterCase


def SketchEvidence(ModeValue: str, IsSuppressed: bool) -> CadDocument:
    Document = AdapterCase("rectangle")
    SketchValue = Document.sketches[0]
    if ModeValue == "payload":
        Original = OpenDocument(KSamplePath)
        EntityValue = next(
            Entity
            for Sketch in Original.sketches
            for Entity in Sketch.entities
            if isinstance(Entity.geometry, NativeGeometry)
            and Entity.geometry.data.get("record_data")
        )
        EntityValue = ReplaceData(
            EntityValue, id="evidence:native", kind=GeometryKind.LINE
        )
        Entities = (*SketchValue.entities, EntityValue)
    else:
        EntityValue = ReplaceData(
            SketchValue.entities[0],
            kind=GeometryKind.NATIVE if ModeValue == "kind" else "future:curve",
        )
        Entities = (EntityValue, *SketchValue.entities[1:])
    return ReplaceData(
        Document,
        sketches=(
            ReplaceData(SketchValue, entities=Entities, suppressed=IsSuppressed),
        ),
    )
