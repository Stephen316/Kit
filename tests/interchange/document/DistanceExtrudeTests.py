from dataclasses import replace as ReplaceValue
from math import pi as CirclePi

from pytest import raises as Raises

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumGeometry import GeometryKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceSpan import GetDistSpan
from interchange.features.DistanceValues import GetDistValues
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter, ParameterValue
from interchange.records.RecordSource import CadSource


# a circle and mixed length units exercise typed distance ownership independently of geometry
def BuildDistExt() -> CadDocument:
    Definition = DistanceExtrude(
        AlongParameterId="along",
        Direction=SpaceVector(0.0, 0.0, 1.0),
        StartOffsetId="offset",
        TaperParameterId="taper",
    )
    Profile = SketchEntity(
        "circle", GeometryKind.KCircle, CircleGeometry(PlaneVector(0.0, 0.0), 3.0)
    )
    return CadDocument(
        source=CadSource("fixture", "extrude", "0" * 64),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(
            Parameter(
                "along",
                "Along",
                ParameterValue(-1.2, ValueKind.KLength, "cm"),
                owner_id="extrude",
            ),
            Parameter(
                "offset",
                "Offset",
                ParameterValue(2.0, ValueKind.KLength, "mm"),
                owner_id="extrude",
            ),
            Parameter(
                "taper",
                "Taper",
                ParameterValue(0.0, ValueKind.KAngle, "rad"),
                owner_id="extrude",
            ),
        ),
        support_planes=(SupportPlane("plane", "Plane", Transform()),),
        sketches=(
            Sketch(
                "profile",
                "Profile",
                "plane",
                (Profile,),
                closed_profile_entity_ids=(("circle",),),
            ),
        ),
        selections=(),
        feature_timeline=(
            FeatureStep(
                id="extrude",
                name="Extrude",
                kind=FeatureKind.KExtrusion,
                order=0,
                sketch_id="profile",
                operation=BooleanOp.KCreate,
                definition=Definition,
                parameter_ids=("along", "offset", "taper"),
            ),
        ),
        bodies=(),
    )


# serialized control references remain exact after parameter edits
def CheckDistRound() -> None:
    Document = BuildDistExt()
    Document.AssertValid()
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    StepValue = Restored.feature_timeline[0]
    Definition = StepValue.definition
    assert isinstance(Definition, DistanceExtrude)
    Params = {Value.id: Value for Value in Restored.parameters}
    Values = GetDistValues(StepValue, Definition, Params)
    assert (Values.LowerMm, Values.UpperMm, Values.OffsetMm) == (-10.0, 2.0, 2.0)
    assert Values.TaperRadians == 0.0 and Values.SecondTaperRadians is None
    Params["along"] = ReplaceValue(
        Params["along"], value=ParameterValue(8.0, ValueKind.KLength, "mm")
    )
    Updated = GetDistValues(StepValue, Definition, Params)
    assert (Updated.LowerMm, Updated.UpperMm) == (2.0, 10.0)
    assert Restored.feature_timeline[0].definition == Definition


# positive native against distance becomes a negative profile relative station
def CheckDistSpan() -> None:
    assert GetDistSpan(7.0, 11.0, 0.0, "two_sided") == (-11.0, 7.0)
    assert GetDistSpan(12.0, None, 0.0, "symmetric_full") == (-6.0, 6.0)
    assert GetDistSpan(12.0, None, 0.0, "symmetric_half") == (-12.0, 12.0)
    assert GetDistSpan(8.0, None, -2.0, "one_sided") == (-2.0, 6.0)
    with Raises(ValueError, match="must be positive"):
        _ = GetDistSpan(7.0, -11.0, 0.0, "two_sided")
    with Raises(ValueError, match="finite distinct"):
        _ = GetDistSpan(0.0, None, 0.0, "one_sided")
    with Raises(ValueError, match="finite distinct"):
        _ = GetDistSpan(10**308, None, 10**308, "one_sided")
    with Raises(ValueError, match="finite axial controls"):
        _ = GetDistSpan(float("inf"), None, 0.0, "one_sided")


# profiles operations and parameter ownership must survive neutral validation
def CheckDistLinks() -> None:
    Document = BuildDistExt()
    StepValue = Document.feature_timeline[0]
    Along, Offset, Taper = Document.parameters
    NoSketch = ReplaceValue(
        Document, feature_timeline=(ReplaceValue(StepValue, sketch_id=None),)
    )
    assert any("requires a profile sketch" in Error for Error in NoSketch.validate())
    WrongOperation = ReplaceValue(
        Document,
        feature_timeline=(ReplaceValue(StepValue, operation=BooleanOp.KCutOperation),),
    )
    assert any(
        "requires a create extrusion feature" in Error
        for Error in WrongOperation.validate()
    )
    Unowned = ReplaceValue(
        Document, parameters=(ReplaceValue(Along, owner_id="other"), Offset, Taper)
    )
    assert any(
        "unlinked or unowned extrusion parameter along" in Error
        for Error in Unowned.validate()
    )
    WrongUnit = ReplaceValue(
        Document,
        parameters=(
            Along,
            Offset,
            ReplaceValue(Taper, value=ParameterValue(1.0, ValueKind.KAngle, "deg")),
        ),
    )
    assert any("unsupported units" in Error for Error in WrongUnit.validate())


# symmetric controls may mirror only the exact same taper reference
def CheckDistModes() -> None:
    Document = BuildDistExt()
    Definition = Document.feature_timeline[0].definition
    assert isinstance(Definition, DistanceExtrude)
    Mirrored = ReplaceValue(
        Definition, SideMode="symmetric_full", SecondTaperId="taper"
    )
    assert Mirrored.TaperParameterId == Mirrored.SecondTaperId
    with Raises(ValueError, match="second taper disagree"):
        _ = ReplaceValue(Mirrored, SecondTaperId="offset")
    with Raises(ValueError, match="must be distinct"):
        _ = ReplaceValue(Definition, StartOffsetId="along")
    with Raises(ValueError, match="unit vector"):
        _ = ReplaceValue(Definition, Direction=SpaceVector(0.0, 0.0, 2.0))
    with Raises(ValueError, match="against parameter disagree"):
        _ = ReplaceValue(Definition, SideMode="two_sided")
    Taper = ReplaceValue(
        Document.parameters[-1],
        value=ParameterValue(CirclePi / 2.0, ValueKind.KAngle, "rad"),
    )
    Invalid = ReplaceValue(Document, parameters=(*Document.parameters[:-1], Taper))
    assert any("less than a right angle" in Error for Error in Invalid.validate())
