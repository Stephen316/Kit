from dataclasses import dataclass as MakeDataClass
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditableExt import EditExtrude, FindEditFrame
from convert.adapters.freecad.EditRead.EditExtrusion import (
    ReadEditDepth,
    ReadShapeEntry,
)
from convert.adapters.freecad.EditRead.EditObjects import FindEditObject, RequireEditObj
from convert.adapters.freecad.EditRead.EditParts import OpenSketchCache, ReadScopedParts
from convert.adapters.freecad.EditRead.EditProfile import CheckEditProf
from convert.adapters.freecad.EditRead.EditSheet import ReadEditText
from convert.adapters.freecad.EditRead.XmlField import EditScalar
from convert.adapters.freecad.Native import NativeObject, ParseObjects
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.geometry.models.Sketch import Sketch
from interchange.records.RecordParameter import Parameter

# generated metadata groups delimit which native objects belong to the bound solid
KProfileRoots = {
    "Parameters": "Spreadsheet::Sheet",
    "KitMetadata": "App::FeaturePython",
    **dict.fromkeys(
        (
            "SupportPlanes",
            "Sketches",
            "Selections",
            "Configurations",
            "FeatureTimeline",
            "Bodies",
        ),
        "App::DocumentObjectGroup",
    ),
}


# additions outside the source profile and body graph cannot be merged into the source snapshot
def CheckProfileSet(Objects: tuple[NativeObject, ...], Document: CadDocument) -> None:
    ObjectTypes = {Value.name: Value.type_id for Value in Objects}
    ExpectedCount = (
        len(KProfileRoots)
        + 3 * len(Document.sketches)
        + len(Document.configurations)
        + len(Document.bodies)
        + 1
    )
    if len(Objects) != ExpectedCount or any(
        ObjectTypes.get(NameValue) != KindValue
        for NameValue, KindValue in KProfileRoots.items()
    ):
        raise ValueError("FreeCAD editable profile native object scope changed")


# live control evidence travels with the exact sidecar needed for independent shape proof
@MakeDataClass(frozen=True, slots=True)
class EditFields:
    DistanceMm: float
    ShapeEntry: str
    SourceText: str
    SketchEntry: str
    EmptyEntries: tuple[str, ...]
    IndependentCaches: tuple[OpenSketchCache, ...]
    ParameterEdits: tuple[Parameter, ...]
    ProfileSketch: Sketch


# reconciling a depth requires an unchanged linked profile and corroborated native controls
def ReadEditFields(
    RootValue: Element,
    DocValue: CadDocument,
    PlanValue: EditExtrude,
    AllowProfile: bool = False,
) -> EditFields | None:
    ProfileFrame = FindEditFrame(DocValue, PlanValue.SketchId)
    if (
        not DocValue.feature_timeline
        or ProfileFrame is None
        or len(DocValue.bodies) != 1
    ):
        raise ValueError(
            "FreeCAD editable extrusion snapshot has an invalid document scope"
        )
    StepValue = DocValue.feature_timeline[-1]
    Definition = StepValue.definition
    SketchValue, PlaneValue = ProfileFrame
    BodyValue = DocValue.bodies[0]
    if (
        not isinstance(Definition, DistanceExtrude)
        or Definition.AlongParameterId != PlanValue.ParameterId
        or Definition.Direction != PlanValue.Direction
        or SketchValue.id != PlanValue.SketchId
        or BodyValue.final_feature_id != StepValue.id
    ):
        raise ValueError(
            "FreeCAD editable extrusion plan disagrees with the embedded document"
        )
    Objects = ParseObjects(RootValue)
    if AllowProfile or PlanValue.LineRing:
        CheckProfileSet(Objects, DocValue)
    Feature = FindEditObject(Objects, StepValue.id)
    if Feature is None or Feature.type_id == "Part::Feature":
        return None
    if Feature.type_id != "Part::Extrusion":
        raise ValueError("FreeCAD editable extrusion object has the wrong native type")
    BodyObj = RequireEditObj(Objects, BodyValue.id, "App::DocumentObjectGroup")
    if EditScalar(BodyObj, "Tip", "App::PropertyLink", "Link") != Feature.name:
        raise ValueError("FreeCAD editable extrusion body tip changed")
    ProfileSketch = CheckEditProf(
        Objects, Feature, SketchValue, PlaneValue, AllowProfile, PlanValue.LineRing
    )
    DepthMm = ReadEditDepth(Feature, PlanValue.Direction)
    SourceText, ParameterEdits = ReadEditText(
        Objects,
        Feature,
        DocValue,
        Definition,
        DepthMm,
        StrictLayout=AllowProfile or PlanValue.LineRing,
    )
    SketchEntry, EmptyEntries, Independent = ReadScopedParts(
        Objects, Feature, DocValue, PlanValue.SketchId
    )
    return EditFields(
        DepthMm,
        ReadShapeEntry(Feature),
        SourceText,
        SketchEntry,
        EmptyEntries,
        Independent,
        ParameterEdits,
        ProfileSketch,
    )
