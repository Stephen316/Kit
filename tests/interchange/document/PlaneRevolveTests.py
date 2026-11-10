# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as ReplaceValue

from pytest import raises as Raises

from interchange.core.Common import FreezeMapping
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumFeatures import FeatureKind
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.features.FeatureStep import FeatureStep
from interchange.geometry.models.Selection import Selection, SelectPathElem
from interchange.geometry.models.SupportPlane import SupportPlane
from interchange.geometry.models.Transform import Transform
from interchange.geometry.models.VectorSpace import SpaceVector
from interchange.records.RecordConfig import Configuration
from interchange.records.RecordSource import CadSource


# a minimal document isolates a nonzero start and ordered plane selection references
def BuildPlaneRev() -> CadDocument:
    Definition = PlaneRevolve(
        AxisSelectionId="axis",
        PlaneSelectionIds=("target-two", "target-one"),
        AxisOrigin=SpaceVector(0.0, 0.0, 0.0),
        AxisDirection=SpaceVector(0.0, -1.0, 0.0),
        StartRadians=0.45,
        EndRadians=2.3,
    )
    return CadDocument(
        source=CadSource("fixture", "revolve", "0" * 64),
        configurations=(Configuration("default", "Default", active=True),),
        parameters=(),
        support_planes=(
            SupportPlane("one", "One", Transform()),
            SupportPlane("two", "Two", Transform()),
        ),
        sketches=(),
        selections=(
            Selection("axis", "Axis", (), query=FreezeMapping({"axis": "Y"})),
            Selection("target-one", "One", (SelectPathElem("support_plane", "one"),)),
            Selection("target-two", "Two", (SelectPathElem("support_plane", "two"),)),
        ),
        feature_timeline=(
            FeatureStep(
                id="sweep",
                name="Sweep",
                kind=FeatureKind.KRevolution,
                order=0,
                definition=Definition,
                selection_ids=("axis", "target-one", "target-two"),
            ),
        ),
        bodies=(),
    )


# independent wire registration must preserve the definition and its selection ordering
def CheckRevRound() -> None:
    Document = BuildPlaneRev()
    Document.AssertValid()
    Decoded = CadDocument.from_json(Document.to_json())
    assert Decoded == Document
    Definition = Decoded.feature_timeline[0].definition
    assert isinstance(Definition, PlaneRevolve)
    assert Definition.StartRadians == 0.45
    assert Definition.PlaneSelectionIds == ("target-two", "target-one")


# dangling plane paths and selections owned by another feature cannot drive a sweep
def CheckRevLinks() -> None:
    Document = BuildPlaneRev()
    StepValue = ReplaceValue(
        Document.feature_timeline[0], selection_ids=("target-one",)
    )
    Broken = ReplaceValue(
        Document,
        feature_timeline=(StepValue,),
        support_planes=Document.support_planes[:1],
        selections=(
            ReplaceValue(Document.selections[0], query=FreezeMapping()),
            *Document.selections[1:],
        ),
    )
    Errors = Broken.validate()
    assert "plane revolution sweep has an unlinked selection axis" in Errors
    assert "plane revolution sweep has an unresolved axis selection" in Errors
    assert (
        "plane revolution sweep has an unresolved plane selection target-two" in Errors
    )


# malformed sweep bounds cannot enter the neutral model
def CheckRevLimits() -> None:
    Definition = BuildPlaneRev().feature_timeline[0].definition
    assert isinstance(Definition, PlaneRevolve)
    with Raises(ValueError, match="unit length"):
        _ = ReplaceValue(Definition, AxisDirection=SpaceVector(0.0, 0.0, 0.0))
    with Raises(ValueError, match="increasing partial turn"):
        _ = ReplaceValue(Definition, StartRadians=3.0)
    with Raises(ValueError, match="finite numbers"):
        _ = ReplaceValue(Definition, EndRadians=float("inf"))
    with Raises(ValueError, match="must be distinct"):
        _ = ReplaceValue(Definition, PlaneSelectionIds=("target-one", "target-one"))
