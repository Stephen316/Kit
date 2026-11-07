# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as ReplaceValue
from math import pi as HalfTurn
from math import tau as FullTurn

from pytest import raises as Raises

from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.enums.EnumValues import ValueKind
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.features.RevolveSpan import GetAngleSpan
from interchange.geometry.models.Selection import Selection
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordParameter import Parameter, ParameterValue
from interchange.records.RecordSource import CadSource


# a minimal feature document isolates owned angle references and an origin axis selection
def BuildAngularRev() -> CadDocument:
    Definition = AngularRevolve(
        AxisSelectionId="axis",
        AlongParameterId="along",
        AxisOrigin=SpaceVector(0.0, 0.0, 0.0),
        AxisDirection=SpaceVector(0.0, -1.0, 0.0),
        SideMode="two_sided",
        AgainstParameterId="against",
    )
    return CadDocument(
        source=CadSource("fixture", "revolve", "0" * 64),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(
            Parameter(
                "along",
                "Along",
                ParameterValue(1.1, ValueKind.KAngle, "rad"),
                owner_id="sweep",
            ),
            Parameter(
                "against",
                "Against",
                ParameterValue(0.3, ValueKind.KAngle, "rad"),
                owner_id="sweep",
            ),
        ),
        support_planes=(),
        sketches=(),
        selections=(Selection("axis", "Axis", (), query=FreezeMapping({"axis": "Y"})),),
        feature_timeline=(
            FeatureStep(
                id="sweep",
                name="Sweep",
                kind=FeatureKind.KRevolution,
                order=0,
                definition=Definition,
                parameter_ids=("along", "against"),
                selection_ids=("axis",),
            ),
        ),
        bodies=(),
    )


# stored references survive serialization and permit edits without changing the definition
def CheckAngularRev() -> None:
    Document = BuildAngularRev()
    Document.AssertValid()
    Decoded = CadDocument.from_json(Document.to_json())
    assert Decoded == Document
    Definition = Decoded.feature_timeline[0].definition
    assert isinstance(Definition, AngularRevolve)
    assert Definition.AlongParameterId == "along"
    assert Definition.AgainstParameterId == "against"
    Updated = ReplaceValue(
        Decoded,
        parameters=(
            ReplaceValue(
                Decoded.parameters[0],
                value=ParameterValue(1.4, ValueKind.KAngle, "rad"),
            ),
            Decoded.parameters[1],
        ),
    )
    Updated.AssertValid()
    assert Updated.feature_timeline[0].definition == Definition


# broken selection links and foreign or wrong unit parameters cannot drive a revolution
def CheckRevRefs() -> None:
    Document = BuildAngularRev()
    StepValue = ReplaceValue(Document.feature_timeline[0], selection_ids=())
    Along, Against = Document.parameters
    Unowned = ReplaceValue(
        Document,
        feature_timeline=(StepValue,),
        parameters=(ReplaceValue(Along, owner_id="other"), Against),
    )
    Errors = Unowned.validate()
    assert "angular revolution sweep has an unlinked axis selection" in Errors
    assert any("unlinked or unowned angle parameter along" in Error for Error in Errors)
    WrongUnit = ReplaceValue(
        Document,
        parameters=(
            Along,
            ReplaceValue(Against, value=ParameterValue(45.0, ValueKind.KAngle, "deg")),
        ),
    )
    assert any(
        "numeric angle in rad for parameter against" in Error
        for Error in WrongUnit.validate()
    )


# all signed and positive side modes must preserve their distinct interval conventions
def CheckAngleSpan() -> None:
    assert GetAngleSpan(-0.4, None, "one_sided") == (-0.4, 0.0)
    assert GetAngleSpan(0.4, None, "one_sided") == (0.0, 0.4)
    assert GetAngleSpan(0.4, 0.2, "two_sided") == (-0.2, 0.4)
    assert GetAngleSpan(HalfTurn, HalfTurn, "symmetric") == (-HalfTurn, HalfTurn)
    assert GetAngleSpan(FullTurn + 5e-11, None, "one_sided") == (0.0, FullTurn + 5e-11)
    with Raises(ValueError, match="at most one turn"):
        GetAngleSpan(FullTurn + 2e-10, None, "one_sided")
    with Raises(ValueError, match="exceed tolerance"):
        GetAngleSpan(1e-9, None, "one_sided")
    with Raises(ValueError, match="must agree"):
        GetAngleSpan(0.4, 0.4000000002, "symmetric")
    with Raises(ValueError, match="must be positive"):
        GetAngleSpan(0.4, -0.2, "two_sided")
    with Raises(ValueError, match="finite numbers"):
        GetAngleSpan(float("inf"), None, "one_sided")


# angular limits are evaluated against parameters during document validation
def CheckRevMode() -> None:
    Document = BuildAngularRev()
    StepValue = Document.feature_timeline[0]
    Definition = StepValue.definition
    assert isinstance(Definition, AngularRevolve)
    with Raises(ValueError, match="side mode and against parameter disagree"):
        ReplaceValue(Definition, SideMode="one_sided")
    with Raises(ValueError, match="must be distinct"):
        ReplaceValue(Definition, AgainstParameterId="along")
    Invalid = ReplaceValue(
        Document,
        feature_timeline=(
            ReplaceValue(
                StepValue, definition=ReplaceValue(Definition, SideMode="symmetric")
            ),
        ),
    )
    assert any(
        "symmetric angular revolution angles must agree" in Error
        for Error in Invalid.validate()
    )
