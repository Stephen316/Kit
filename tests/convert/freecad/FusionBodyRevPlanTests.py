# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from dataclasses import replace as Replace

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad.EditBodyRev.BodyRevPlan import ReadBodyRev
from convert.formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.Selection import SelectPathElem
from interchange.geometry.models.VectorSpace import SpaceVector
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# independent native controls cover an origin line and an offset perpendicular line
KBodyRevCases = (
    (
        "revolveaxes-a83b542c4a07/brep_edge.f3d",
        239,
        2,
        (0.0, 30.0, 0.0),
        (0.0, 0.0, 0.0),
    ),
    (
        "revolveaxes-14700158dba9/brep_edge_offset_x.f3d",
        238,
        3,
        (48.0, 0.0, 0.0),
        (11.0, 0.0, 0.0),
    ),
)


# both native controls retain their independently proven source line and directed axis
@KRequiresCodec
@Pytest.mark.parametrize("SampleName,LineKey,EdgeIndex,Start,Finish", KBodyRevCases)
def TestBodyRevPlan(
    SampleName: str,
    LineKey: int,
    EdgeIndex: int,
    Start: tuple[float, ...],
    Finish: tuple[float, ...],
) -> None:
    Original = OpenDocument(KStudyPath / SampleName, StrictMode=False)
    DocValue = CadDocument.from_json(Original.to_json())
    FeatureValue = DocValue.feature_timeline[-1]
    PlanValue = ReadBodyRev(DocValue, FeatureValue)
    assert PlanValue is not None
    assert PlanValue.Extrude.DistanceMm == 5.0 and PlanValue.Revolve.AngleDeg == 73.0
    assert PlanValue.AxisLineId == f"fusion-sketch-entity-{LineKey}"
    assert PlanValue.AxisEdgeId == f"{PlanValue.SourceBodyId}-prism-edge-{EdgeIndex}"
    assert PlanValue.AxisStart == SpaceVector(*Start)
    assert PlanValue.AxisEnd == SpaceVector(*Finish)
    assert PlanValue.AxisSense == -1 and len(PlanValue.ProfilePairs) == 4
    assert DocValue.brep == JoinRevModels(
        (PlanValue.ExtrudeModel, PlanValue.RevolveModel)
    )
    assert tuple(Value.id for Value in DocValue.bodies) == (
        PlanValue.SourceBodyId,
        PlanValue.ResultBodyId,
    )


# inconsistent path or native creator evidence cannot select a nearby edge by geometry
@KRequiresCodec
def TestBadBodyAxis() -> None:
    DocValue = OpenDocument(KStudyPath / KBodyRevCases[0][0], StrictMode=False)
    FeatureValue = DocValue.feature_timeline[-1]
    (SelectionValue,) = DocValue.selections
    Source, Result = DocValue.bodies
    EdgeId = SelectionValue.path[1].entity_id
    WrongEdge = Replace(
        SelectionValue,
        path=(
            SelectionValue.path[0],
            SelectPathElem("edge", f"{Source.id}-prism-edge-1"),
        ),
    )
    WrongBody = Replace(
        SelectionValue,
        path=(SelectPathElem("body", Result.id), SelectPathElem("edge", EdgeId)),
    )
    assert SelectionValue.provenance is not None
    LostAsm = Replace(
        SelectionValue,
        provenance=Replace(
            SelectionValue.provenance, spans=SelectionValue.provenance.spans[:-1]
        ),
    )
    for Invalid in (WrongEdge, WrongBody, LostAsm):
        assert (
            ReadBodyRev(Replace(DocValue, selections=(Invalid,)), FeatureValue) is None
        )


# stale aggregate geometry and unowned controls must fail before native emission
@KRequiresCodec
def TestStaleRev() -> None:
    DocValue = OpenDocument(KStudyPath / KBodyRevCases[0][0], StrictMode=False)
    FeatureValue = DocValue.feature_timeline[-1]
    PlanValue = ReadBodyRev(DocValue, FeatureValue)
    assert PlanValue is not None
    BadParam = Replace(DocValue.parameters[0], owner_id="")
    Broken = (
        Replace(DocValue, parameters=(BadParam, *DocValue.parameters[1:])),
        Replace(DocValue, brep=PlanValue.RevolveModel),
        Replace(DocValue, bodies=DocValue.bodies[::-1]),
    )
    for Value in Broken:
        assert ReadBodyRev(Value, FeatureValue) is None
