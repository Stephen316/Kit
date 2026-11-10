# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace
from math import pi as CirclePi

from pytest import approx as Approx, raises as Raises

from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.BoundPlaneValues import GetDatumFrame
from interchange.features.FeatureBoundPlane import BoundDatum
from interchange.features.FeatureKinds import RefPlaneFeature
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter, ParameterValue
from interchange.records.RecordSource import CadSource

# a nondefault basis makes a global offset or rotation fail visibly
KPlaneFrame = Transform(
    SpaceVector(3, 4, 5),
    SpaceVector(0, 1, 0),
    SpaceVector(0, 0, 1),
    SpaceVector(1, 0, 0),
)


# saved planes and their independently owned parameters share one editable document
def PlaneDocument(Method: str) -> CadDocument:
    Scalar = (
        ParameterValue(CirclePi / 2, ValueKind.KAngle, "rad")
        if Method == "angle"
        else ParameterValue(-2.5, ValueKind.KLength, "cm")
    )
    Definition = BoundDatum("datum", "scalar", "extra", Method, KPlaneFrame)
    StepValue = FeatureStep(
        "plane",
        "Plane",
        FeatureKind.KReference,
        0,
        parameter_ids=("extra", "scalar"),
        definition=Definition,
    )
    Params = (
        Parameter("scalar", "Scalar", Scalar, owner_id=StepValue.id),
        Parameter(
            "extra",
            "Extra offset",
            ParameterValue(0, ValueKind.KLength, "mm"),
            owner_id=StepValue.id,
        ),
    )
    Frame = GetDatumFrame(StepValue, Definition, {Value.id: Value for Value in Params})
    return CadDocument(
        CadSource("fixture", "plane", "0" * 64),
        (Configuration("default", "Default", active=True),),
        Params,
        (SupportPlane("datum", "Plane", Frame),),
        (),
        (),
        (StepValue,),
        (),
    )


# signed displacement follows the authored normal and roundtrips through the wire schema
def TestBoundOffset() -> None:
    Document = PlaneDocument("offset")
    PlaneValue = Document.support_planes[0]
    assert PlaneValue.transform == Replace(KPlaneFrame, origin=SpaceVector(-22, 4, 5))
    Restored = CadDocument.from_json(Document.to_json())
    assert Restored == Document
    assert Restored.validate() == ()
    assert isinstance(Restored.feature_timeline[0].definition, BoundDatum)


# signed angle edits preserve the reference frame and require refreshed cached geometry
def TestBoundAngle() -> None:
    Document = PlaneDocument("angle")
    PlaneValue = Document.support_planes[0]
    Frame = PlaneValue.transform
    assert Frame.origin == KPlaneFrame.origin and Frame.x_axis == KPlaneFrame.x_axis
    assert (Frame.y_axis.x, Frame.y_axis.y, Frame.y_axis.z) == Approx((1, 0, 0))
    assert (Frame.z_axis.x, Frame.z_axis.y, Frame.z_axis.z) == Approx((0, 0, -1))
    StepValue = Document.feature_timeline[0]
    Definition = StepValue.definition
    assert isinstance(Definition, BoundDatum)
    Scalar, Extra = Document.parameters
    NewParam = Replace(
        Scalar, value=ParameterValue(-CirclePi / 3, ValueKind.KAngle, "rad")
    )
    Edited = Replace(Document, parameters=(NewParam, Extra))
    assert any(
        "disagree with its support frame" in Value for Value in Edited.validate()
    )
    Updated = GetDatumFrame(
        StepValue, Definition, {Value.id: Value for Value in Edited.parameters}
    )
    Edited = Replace(Edited, support_planes=(Replace(PlaneValue, transform=Updated),))
    assert Edited.validate() == ()
    assert CadDocument.from_json(Edited.to_json()) == Edited
    assert Updated.z_axis.z == Approx(0.8660254037844386)


# exact ownership and dimensions stop unrelated parameters from moving a support plane
def TestBoundParams() -> None:
    Document = PlaneDocument("angle")
    StepValue = Document.feature_timeline[0]
    Definition = StepValue.definition
    assert isinstance(Definition, BoundDatum)
    Scalar, Extra = Document.parameters
    for BadScalar, BadExtra in (
        (Replace(Scalar, owner_id="different"), Extra),
        (Replace(Scalar, value=ParameterValue(5.0, ValueKind.KLength, "mm")), Extra),
        (Replace(Scalar, value=ParameterValue(5.0, ValueKind.KAngle, "mm")), Extra),
        (
            Replace(
                Scalar, value=ParameterValue(float("inf"), ValueKind.KAngle, "rad")
            ),
            Extra,
        ),
        (Scalar, Replace(Extra, value=ParameterValue(0.25, ValueKind.KLength, "mm"))),
    ):
        with Raises(ValueError, match="construction plane"):
            _ = GetDatumFrame(
                StepValue, Definition, {Scalar.id: BadScalar, Extra.id: BadExtra}
            )
    with Raises(ValueError, match="reference feature"):
        _ = GetDatumFrame(
            Replace(StepValue, kind=FeatureKind.KNative),
            Definition,
            {Scalar.id: Scalar, Extra.id: Extra},
        )


# method specific source tolerances accept numerical noise while rejecting stale poses
def TestBoundFrame() -> None:
    for Method, Delta in (("offset", 1e-9), ("angle", 1e-8)):
        Document = PlaneDocument(Method)
        PlaneValue = Document.support_planes[0]
        Frame = PlaneValue.transform
        for Movement, Valid in ((0.5 * Delta, True), (2.0 * Delta, False)):
            Moved = Replace(
                Frame, origin=Replace(Frame.origin, y=Frame.origin.y + Movement)
            )
            Changed = Replace(
                Document, support_planes=(Replace(PlaneValue, transform=Moved),)
            )
            assert (Changed.validate() == ()) is Valid
        Missing = Replace(Document, support_planes=())
        assert any("missing its support frame" in Value for Value in Missing.validate())


# authored zero poses must be finite right handed frames with distinct controls
def TestBoundShape() -> None:
    Reflected = Replace(KPlaneFrame, z_axis=SpaceVector(-1, 0, 0))
    with Raises(ValueError, match="reference frame"):
        BoundDatum("datum", "scalar", "extra", "offset", Reflected)
    with Raises(ValueError, match="distinct"):
        BoundDatum("datum", "scalar", "scalar", "offset", KPlaneFrame)
    with Raises(ValueError, match="method"):
        BoundDatum("datum", "scalar", "extra", "parallel", KPlaneFrame)


# the new definition keeps the legacy portable reference plane type independent
def TestLegacyPlane() -> None:
    Document = PlaneDocument("offset")
    Definition = RefPlaneFeature(
        "datum", "old-reference", ParameterValue(2.0, ValueKind.KLength, "mm")
    )
    Original = Replace(
        Document,
        feature_timeline=(
            Replace(Document.feature_timeline[0], definition=Definition),
        ),
    )
    Payload = Original.to_json()
    assert '"ReferencePlaneFeature"' in Payload
    assert CadDocument.from_json(Payload) == Original
    assert Original.validate() == ()
