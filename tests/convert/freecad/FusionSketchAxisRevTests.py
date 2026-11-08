# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.


from dataclasses import replace as Replace

import pytest as Pytest

from convert import open_document as OpenDocument
from convert.adapters.freecad.Brep import BrepModelBrep
from convert.adapters.freecad.EditAxisRev.AxisProfile import ReadAxisProfile
from convert.adapters.freecad.EditAxisRev.AxisRevPlan import ReadAxisRev
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.GeometryCurves import PointGeometry
from interchange.geometry.models.VectorPlane import PlaneVector
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the saved source contrast uses the same selected line with opposite directed endpoints
KAxisCases = KStudyPath / "revolveaxes-a83b542c4a07"


# source ids and axis direction stay stable across neutral serialization
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "Expected"), (("sketch_line", 1), ("sketch_line_reversed", -1))
)
def CheckAxisPlan(Capture: str, Expected: int) -> None:
    DocValue = OpenDocument(KAxisCases / f"{Capture}.f3d", strict=False)
    StepValue = DocValue.feature_timeline[-1]
    PlanValue = ReadAxisRev(DocValue, StepValue)
    assert PlanValue is not None
    assert PlanValue.AxisSense == Expected
    assert PlanValue.Revolve.AngleDeg == 73.0
    assert PlanValue.AxisStart == PlanValue.Revolve.AxisOrigin
    assert (PlanValue.AxisStart.x, PlanValue.AxisEnd.x) == Pytest.approx(
        (10.0, 27.888543819998315)[::Expected]
    )
    assert PlanValue.AxisPointIds == (
        "fusion-sketch-entity-228",
        "fusion-sketch-entity-230",
    )
    assert PlanValue.AxisLineId == "fusion-sketch-entity-232"
    assert PlanValue.AxisSketchId == "fusion-sketch-202"
    assert PlanValue.Revolve.SketchId == "fusion-sketch-239"
    assert DocValue.brep is not None and BrepModelBrep(DocValue.brep)
    Restored = CadDocument.FromJson(DocValue.ToJson())
    assert ReadAxisRev(Restored, Restored.feature_timeline[-1]) == PlanValue


# native identities remain distinct across all four geometric profile joins
@KRequiresCodec
def CheckAxisPairs() -> None:
    DocValue = OpenDocument(KAxisCases / "sketch_line.f3d", strict=False)
    StepValue = DocValue.feature_timeline[-1]
    SketchValue = DocValue.sketches[1]
    Pairs = ReadAxisProfile(StepValue, SketchValue)
    assert Pairs == tuple(
        (f"fusion-sketch-entity-{First}", f"fusion-sketch-entity-{Second}")
        for First, Second in ((274, 280), (282, 288), (290, 264), (266, 272))
    )
    Changed = Replace(
        SketchValue,
        entities=tuple(
            (
                Replace(Value, geometry=PointGeometry(PlaneVector(0.0, 0.0)))
                if Value.id == Pairs[0][0]
                else Value
            )
            for Value in SketchValue.entities
        ),
    )
    with Pytest.raises(ValueError, match="endpoint provenance disagrees"):
        ReadAxisProfile(StepValue, Changed)


# unsupported edge sources and stale native scope cannot seed editable geometry
@KRequiresCodec
def CheckAxisGuards() -> None:
    EdgeDoc = OpenDocument(KAxisCases / "brep_edge.f3d", strict=False)
    assert ReadAxisRev(EdgeDoc, EdgeDoc.feature_timeline[-1]) is None
    DocValue = OpenDocument(KAxisCases / "sketch_line.f3d", strict=False)
    StepValue = DocValue.feature_timeline[-1]
    (PickValue,) = DocValue.selections
    WrongPick = Replace(PickValue, path=PickValue.path[::-1])
    assert ReadAxisRev(Replace(DocValue, selections=(WrongPick,)), StepValue) is None
    AxisSketch, Profile = DocValue.sketches
    Invalid = Replace(
        AxisSketch,
        entities=tuple(
            Replace(Value, construction=False) for Value in AxisSketch.entities
        ),
    )
    assert (
        ReadAxisRev(Replace(DocValue, sketches=(Invalid, Profile)), StepValue) is None
    )
    (BodyValue,) = DocValue.bodies
    assert BodyValue.topology is not None
    Stale = Replace(BodyValue, topology=Replace(BodyValue.topology, volume=1.0))
    assert ReadAxisRev(Replace(DocValue, bodies=(Stale,)), StepValue) is None
