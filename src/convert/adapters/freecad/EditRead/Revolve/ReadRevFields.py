from dataclasses import dataclass as MakeDataClass
from math import tau as FullTurn
from xml.etree.ElementTree import Element

from convert.adapters.freecad.EditableRev import EditRevolve
from convert.adapters.freecad.EditRev.RevAngles import ReadRevAngles
from convert.adapters.freecad.EditRev.RevScope import ReadRevScope
from convert.adapters.freecad.EditRead.Revolve.RevControls import CheckRevValues
from convert.adapters.freecad.EditRev.RevExpressions import RevExpressions
from convert.adapters.freecad.EditRead.Revolve.RevGraph import ReadRevGraph
from convert.adapters.freecad.EditRead.Revolve.RevPose import CheckRevPose
from convert.adapters.freecad.EditRead.Revolve.RevSheet import ReadRevSheet
from convert.adapters.freecad.EditRead.Sketch.RingProof import ReadRingProfile
from convert.adapters.freecad.Native import ParseObjects
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Sketch import Sketch


# only corroborated native parameters and shape references may reach neutral rebuilding
@MakeDataClass(frozen=True, slots=True)
class RevFields:
    AlongRad: float
    AgainstRad: float | None
    ProfileSketch: Sketch
    ShapeEntry: str
    SketchEntry: str
    EmptyEntries: tuple[str, ...]
    AlongText: str
    AgainstText: str | None


# the native feature and its spreadsheet must agree before any saved edit is applied
def ReadRevFields(
    RootValue: Element, DocValue: CadDocument, PlanValue: EditRevolve
) -> RevFields:
    if not DocValue.feature_timeline:
        raise ValueError("FreeCAD editable Revolve source timeline is missing")
    StepValue = DocValue.feature_timeline[-1]
    Definition = StepValue.definition
    Original, PlaneValue, _ = ReadRevScope(DocValue, StepValue)
    if (
        not isinstance(Definition, AngularRevolve)
        or Original.id != PlanValue.SketchId
        or Definition.AlongParameterId != PlanValue.AngleParamId
        or Definition.AgainstParameterId != PlanValue.AgainstParamId
        or Definition.AxisOrigin != PlanValue.AxisOrigin
        or Definition.AxisDirection != PlanValue.AxisDirection
        or PlanValue.Symmetric != (Definition.SideMode != "one_sided")
        or PlanValue.AngleScale != (2.0 if Definition.SideMode == "symmetric" else 1.0)
    ):
        raise ValueError("FreeCAD editable Revolve plan disagrees with its source")
    Before = ReadRevAngles(StepValue, Definition, DocValue.parameters)
    Graph = ReadRevGraph(ParseObjects(RootValue), DocValue, Original, PlaneValue)
    Edited = ReadRingProfile(Graph.Profile, Original, AllowProfile=True)
    Aliases, Along, Against, AlongText, AgainstText = ReadRevSheet(
        Graph.Sheet, DocValue.parameters, PlanValue
    )
    Start, EndValue = GetAngleSpan(Along, Against, Definition.SideMode)
    if EndValue - Start > FullTurn:
        raise ValueError("FreeCAD editable Revolve exceeds one turn")
    CheckRevValues(
        Graph.Feature, PlanValue, RevExpressions(PlanValue, Aliases), Along, Against
    )
    IsSeed = not Graph.SketchEntry
    if IsSeed and ((Along, Against) != Before or Edited is not Original):
        raise ValueError(
            "FreeCAD editable Revolve edit is missing its saved profile cache"
        )
    CheckRevPose(Graph.Feature, PlanValue, Along, Against, IsSeed)
    return RevFields(
        Along,
        Against,
        Edited,
        Graph.ShapeEntry,
        Graph.SketchEntry,
        Graph.EmptyEntries,
        AlongText,
        AgainstText,
    )
