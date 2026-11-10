# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as ReplaceValue
from math import cos as Cosine, pi as PiValue, sin as SineValue

from pytest import approx as Approx, mark as Marker, raises as Raises

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from interchange.enums.EnumGeometry import GeometryKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.DistanceValues import DistExtValues
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeatureStep import FeatureStep
from interchange.features.PlaneExtValues import GetPlaneExt
from interchange.geometry.models.GeometryCurves import CircleGeometry
from interchange.geometry.models.Selection import SelectPathElem, Selection
from interchange.geometry.models.Sketch import Sketch, SketchEntity
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorPlane import PlaneVector
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter, ParameterValue
from interchange.records.RecordSource import CadSource


# rotated frames and lateral plane movement separate projection from global coordinates
def BuildPlaneDoc(RoleValue: str) -> CadDocument:
    Frame = Transform(
        SpaceVector(4.0, 10.0, -2.0),
        SpaceVector(1.0, 0.0, 0.0),
        SpaceVector(0.0, 0.8, -0.6),
        SpaceVector(0.0, 0.6, 0.8),
    )
    Limit = ReplaceValue(Frame, origin=SpaceVector(7.0, 23.0, 7.0))
    Params: tuple[Parameter, ...] = (
        Parameter(
            "offset",
            "Offset",
            ParameterValue(0.25, ValueKind.KLength, "cm"),
            owner_id="extrude",
        ),
        Parameter(
            "taper",
            "Taper",
            ParameterValue(0.0, ValueKind.KAngle, "rad"),
            owner_id="extrude",
        ),
    )
    LengthId = None
    if RoleValue == "start":
        LengthId = "length"
        Params += (
            Parameter(
                LengthId,
                "Length",
                ParameterValue(0.5, ValueKind.KLength, "in"),
                owner_id="extrude",
            ),
        )
    Profile = SketchEntity(
        "circle", GeometryKind.KCircle, CircleGeometry(PlaneVector(0.0, 0.0), 3.0)
    )
    Definition = PlaneExtrude(
        "pick", Frame.z_axis, RoleValue, "offset", LengthId, "taper"
    )
    return CadDocument(
        source=CadSource("fixture", "plane-extrude", "0" * 64),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=Params,
        support_planes=(
            SupportPlane("profile-plane", "Profile", Frame),
            SupportPlane("limit", "Limit", Limit),
        ),
        sketches=(
            Sketch(
                "profile",
                "Profile",
                "profile-plane",
                (Profile,),
                closed_profile_entity_ids=(("circle",),),
            ),
        ),
        selections=(
            Selection("pick", "Limit", (SelectPathElem("support_plane", "limit"),)),
        ),
        feature_timeline=(
            FeatureStep(
                "extrude",
                "Extrude",
                FeatureKind.KExtrusion,
                0,
                sketch_id="profile",
                operation=BooleanOp.KCreate,
                definition=Definition,
                parameter_ids=tuple(Value.id for Value in Params),
                selection_ids=("pick",),
            ),
        ),
        bodies=(),
    )


# direct extent evaluation lets tests inspect edited stations as well as validation
def EvalExtent(Document: CadDocument) -> DistExtValues:
    StepValue = Document.feature_timeline[0]
    Definition = StepValue.definition
    assert isinstance(Definition, PlaneExtrude)
    return GetPlaneExt(
        StepValue,
        Definition,
        {Value.id: Value for Value in Document.parameters},
        {Value.id: Value for Value in Document.selections},
        {Value.id: Value for Value in Document.support_planes},
        {Value.id: Value for Value in Document.sketches},
    )


# offset length and moved support planes must remain live after serialization
@Marker.parametrize(
    "RoleValue,Expected", (("start", (17.5, 30.2, 17.5)), ("end", (0.0, 17.5, 0.0)))
)
def CheckPlaneWire(RoleValue: str, Expected: tuple[float, ...]) -> None:
    Document = BuildPlaneDoc(RoleValue)
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    assert Restored.validate() == ()
    Values = EvalExtent(Restored)
    assert (Values.LowerMm, Values.UpperMm, Values.OffsetMm) == Approx(Expected)
    assert Values.TaperRadians == 0.0 and Values.SecondTaperRadians is None
    Offset, *Remaining = Restored.parameters
    Edited = ReplaceValue(Offset, value=ParameterValue(4.0, ValueKind.KLength, "mm"))
    EditedDoc = ReplaceValue(Restored, parameters=(Edited, *Remaining))
    assert EvalExtent(EditedDoc).UpperMm == Approx(Expected[1] + 1.5)
    Profile, Limit = Restored.support_planes
    Moved = ReplaceValue(
        Limit,
        transform=ReplaceValue(Limit.transform, origin=SpaceVector(7.0, 26.0, 11.0)),
    )
    MovedDoc = ReplaceValue(EditedDoc, support_planes=(Profile, Moved))
    assert EvalExtent(MovedDoc).UpperMm == Approx(Expected[1] + 6.5)
    assert MovedDoc.feature_timeline == Restored.feature_timeline


# two nearly aligned normals still need a component wise coincidence check
@Marker.parametrize(
    "Angle,Accepted",
    ((1e-11, True), (5e-8, False), (PiValue / 2.0, False), (PiValue, False)),
)
def CheckPlaneAlign(Angle: float, Accepted: bool) -> None:
    Document = BuildPlaneDoc("end")
    Profile, Limit = Document.support_planes
    CosValue, SinValue = Cosine(Angle), SineValue(Angle)
    Frame = ReplaceValue(
        Limit.transform,
        y_axis=SpaceVector(
            0.0, 0.8 * CosValue + 0.6 * SinValue, -0.6 * CosValue + 0.8 * SinValue
        ),
        z_axis=SpaceVector(
            0.0, 0.6 * CosValue - 0.8 * SinValue, 0.8 * CosValue + 0.6 * SinValue
        ),
    )
    Edited = ReplaceValue(
        Document, support_planes=(Profile, ReplaceValue(Limit, transform=Frame))
    )
    if Accepted:
        assert EvalExtent(Edited).UpperMm == Approx(17.5)
    else:
        with Raises(ValueError, match="co-directed"):
            _ = EvalExtent(Edited)


# local selection paths and current feature state are part of the editable contract
def CheckPlaneLinks() -> None:
    Document = BuildPlaneDoc("end")
    StepValue = Document.feature_timeline[0]
    SelectionValue = Document.selections[0]
    Foreign = ReplaceValue(
        SelectionValue,
        path=(SelectPathElem("component", "foreign"), *SelectionValue.path),
    )
    Invalid = ReplaceValue(Document, selections=(Foreign,))
    assert any("local support plane selection" in Error for Error in Invalid.validate())
    Invalid = ReplaceValue(
        Document, feature_timeline=(ReplaceValue(StepValue, selection_ids=()),)
    )
    assert any("local support plane selection" in Error for Error in Invalid.validate())
    Invalid = ReplaceValue(
        Document, feature_timeline=(ReplaceValue(StepValue, sketch_id=None),)
    )
    assert any("requires a profile sketch" in Error for Error in Invalid.validate())
    Invalid = ReplaceValue(
        Document,
        feature_timeline=(ReplaceValue(StepValue, operation=BooleanOp.KCutOperation),),
    )
    assert any("requires a create extrusion" in Error for Error in Invalid.validate())
    Profile, Limit = Document.support_planes
    Behind = ReplaceValue(
        Limit, transform=ReplaceValue(Limit.transform, origin=Profile.transform.origin)
    )
    Invalid = ReplaceValue(Document, support_planes=(Profile, Behind))
    assert any("forward from the profile" in Error for Error in Invalid.validate())


# edits outside the verified parameter and positive extent conventions fail validation
def CheckPlaneParam() -> None:
    Document = BuildPlaneDoc("start")
    Offset, Taper, Length = Document.parameters
    for Params, TextValue in (
        ((ReplaceValue(Offset, owner_id="other"), Taper, Length), "unowned"),
        (
            (
                ReplaceValue(
                    Offset, value=ParameterValue(-1.0, ValueKind.KLength, "mm")
                ),
                Taper,
                Length,
            ),
            "nonnegative",
        ),
        (
            (
                Offset,
                ReplaceValue(
                    Taper, value=ParameterValue(0.01, ValueKind.KAngle, "rad")
                ),
                Length,
            ),
            "zero taper",
        ),
        (
            (
                Offset,
                Taper,
                ReplaceValue(
                    Length, value=ParameterValue(0.0, ValueKind.KLength, "mm")
                ),
            ),
            "positively separated",
        ),
        (
            (
                Offset,
                Taper,
                ReplaceValue(
                    Length, value=ParameterValue(1.0, ValueKind.KLength, "rad")
                ),
            ),
            "unsupported units",
        ),
    ):
        with Raises(ValueError, match=TextValue):
            _ = EvalExtent(ReplaceValue(Document, parameters=Params))
    Definition = Document.feature_timeline[0].definition
    assert isinstance(Definition, PlaneExtrude)
    with Raises(ValueError, match="length parameter disagree"):
        _ = ReplaceValue(Definition, LimitRole="end")
    with Raises(ValueError, match="roles must be distinct"):
        _ = ReplaceValue(Definition, LengthParameterId="offset")
    with Raises(ValueError, match="unit vector"):
        _ = ReplaceValue(Definition, Direction=SpaceVector(0.0, 0.0, 2.0))
