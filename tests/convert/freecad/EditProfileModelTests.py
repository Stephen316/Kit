# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace
from io import BytesIO
from math import pi as HalfTurn
from pathlib import Path as FilePath
from zipfile import ZipFile

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.adapters.freecad import build_fcstd_archive as BuildFcstdArchive
from convert.adapters.freecad import document_to_manifest as DocToManifest
from convert.adapters.freecad.ApplyDepthEdit import ApplyDepthEdit
from convert.adapters.freecad.ArchiveEditPlan import ReadArchiveEdit
from convert.adapters.freecad.EditExtProfile import GetCenterPoint, GetEditCircle
from interchange.document.models.DocumentModel import CadDocument
from interchange.geometry.models.GeometryCurves import CircleGeometry, PointGeometry
from interchange.geometry.models.Sketch import Sketch
from interchange.geometry.models.VectorPlane import PlaneVector

# actual fusion fixtures preserve native identities and exact initial geometry
KStudyRoot = FilePath(__file__).parents[3] / "re/Fusion/Study"

# positive and negative source profiles use the same selected sketch encoding
KExtentsDir = KStudyRoot / "extents-f0f33a9a605f"


# a saved profile can move only its selected circle and exact native center helper
def ChangeProfile(Original: Sketch, Profile: CircleGeometry) -> Sketch:
    Center = GetCenterPoint(Original)
    assert Center is not None
    Selected = Original.closed_profile_entity_ids[0][0]
    Entities = tuple(
        (
            Replace(Value, geometry=Profile)
            if Value.id == Selected
            else (
                Replace(Value, geometry=PointGeometry(Profile.center))
                if Value.id == Center.id
                else Value
            )
        )
        for Value in Original.entities
    )
    return Replace(Original, entities=Entities)


# regenerated solids must agree with both the editable writer and unchanged source identities
def VerifyRebuilt(
    Original: CadDocument, Updated: CadDocument, Profile: CircleGeometry, DepthMm: float
) -> None:
    Updated.assert_valid()
    PlanValue = ReadArchiveEdit(Updated)
    assert PlanValue is not None and PlanValue[1].DistanceMm == Pytest.approx(DepthMm)
    assert Updated.source is Original.source
    assert Updated.feature_timeline is Original.feature_timeline
    assert Updated.brep_payloads is Original.brep_payloads
    assert Updated.bodies[0].id == Original.bodies[0].id
    assert Updated.bodies[0].provenance is Original.bodies[0].provenance
    Topology = Updated.bodies[0].topology
    assert Topology.volume == Pytest.approx(HalfTurn * Profile.radius**2 * abs(DepthMm))
    assert Topology.surface_area == Pytest.approx(
        2 * HalfTurn * Profile.radius * (Profile.radius + abs(DepthMm))
    )
    Bounds = Topology.bounding_box
    assert Bounds is not None
    assert Bounds.minimum.x == Pytest.approx(Profile.center.x - Profile.radius)
    assert Bounds.maximum.y == Pytest.approx(Profile.center.y + Profile.radius)
    assert Bounds.minimum.z == Pytest.approx(min(0.0, DepthMm))
    assert Bounds.maximum.z == Pytest.approx(max(0.0, DepthMm))


# profile only edits cannot manufacture a depth change from native decimal roundoff
@Pytest.mark.parametrize(
    "Profile",
    (
        CircleGeometry(PlaneVector(0.0, 0.0), 14.0),
        CircleGeometry(PlaneVector(4.0, -3.0), 10.0),
    ),
)
def TestProfileOnly(Profile: CircleGeometry) -> None:
    Original = OpenDocument(KExtentsDir / "distance_positive.f3d", StrictMode=False)
    Feature = Original.feature_timeline[-1]
    SketchValue = Original.sketches[0]
    Frame = Original.support_planes[0].transform
    PlanValue = ReadArchiveEdit(Original)
    assert PlanValue is not None
    Baseline = GetEditCircle(Feature, SketchValue)
    assert Baseline is not None
    assert (
        ApplyDepthEdit(
            Original,
            PlanValue[1].ParameterId,
            None,
            PlanValue[1].DistanceMm + 1e-10,
            Baseline,
            Frame,
            EditedSketch=SketchValue,
        )
        is Original
    )
    Edited = ChangeProfile(SketchValue, Profile)
    Updated = ApplyDepthEdit(
        Original,
        PlanValue[1].ParameterId,
        None,
        PlanValue[1].DistanceMm + 1e-10,
        Profile,
        Frame,
        EditedSketch=Edited,
    )
    assert Updated.parameters is Original.parameters
    assert Updated.sketches[0] is Edited
    VerifyRebuilt(Original, Updated, Profile, PlanValue[1].DistanceMm)


# a simultaneous depth and profile edit must still emit a real editable extrusion
def TestSigned() -> None:
    Original = OpenDocument(KExtentsDir / "distance_negative.f3d", StrictMode=False)
    PlanValue = ReadArchiveEdit(Original)
    assert PlanValue is not None
    Profile = CircleGeometry(PlaneVector(3.0, -4.0), 13.0)
    Edited = ChangeProfile(Original.sketches[0], Profile)
    Updated = ApplyDepthEdit(
        Original,
        PlanValue[1].ParameterId,
        "-25 mm",
        -25.0,
        Profile,
        Original.support_planes[0].transform,
        EditedSketch=Edited,
    )
    VerifyRebuilt(Original, Updated, Profile, -25.0)
    OldParam = Original.parameter(PlanValue[1].ParameterId)
    NewParam = Updated.parameter(PlanValue[1].ParameterId)
    assert NewParam.owner_id == OldParam.owner_id
    assert NewParam.provenance is OldParam.provenance
    Emitted: set[str] = set()
    Payload = BuildFcstdArchive(DocToManifest(Updated), editable_features=Emitted)
    assert Emitted == {PlanValue[0]}
    with ZipFile(BytesIO(Payload)) as Archive:
        assert any(NameValue.endswith(".Shape.brp") for NameValue in Archive.namelist())


# a changed driver and profile preserve the dependent source formula and auxiliary sketch
def TestFormProfile() -> None:
    Original = OpenDocument(
        KStudyRoot / "holdouts-f8c508a73323/expression_depth.f3d", StrictMode=False
    )
    PlanValue = ReadArchiveEdit(Original)
    assert PlanValue is not None and PlanValue[1].HasFormula
    SketchValue = Original.sketch(PlanValue[1].SketchId)
    SourceParam = Original.parameter(PlanValue[1].ParameterId)
    assert SourceParam.expression is not None
    Driver = Original.parameter(SourceParam.expression.parameter_ids[0])
    assert Driver.expression is not None
    Profile = CircleGeometry(PlaneVector(2.0, -3.0), 15.0)
    Edits = (
        Replace(
            Driver,
            value=Replace(Driver.value, value=1.25),
            expression=Replace(Driver.expression, source="12.5 mm"),
        ),
        Replace(SourceParam, value=Replace(SourceParam.value, value=2.6)),
    )
    Updated = ApplyDepthEdit(
        Original,
        PlanValue[1].ParameterId,
        SourceParam.expression.source,
        26.0,
        Profile,
        Original.plane(SketchValue.support_plane_id).transform,
        Edits,
        ChangeProfile(SketchValue, Profile),
    )
    VerifyRebuilt(Original, Updated, Profile, 26.0)
    assert Updated.parameter(SourceParam.id).expression is SourceParam.expression
    assert Updated.sketches[0] is Original.sketches[0]


# changing a circle without its exact source center point would lose sketch incidence
def TestDetached() -> None:
    Original = OpenDocument(KExtentsDir / "distance_positive.f3d", StrictMode=False)
    PlanValue = ReadArchiveEdit(Original)
    assert PlanValue is not None
    SketchValue = Original.sketches[0]
    Profile = CircleGeometry(PlaneVector(3.0, -4.0), 10.0)
    Selected = SketchValue.closed_profile_entity_ids[0][0]
    Edited = Replace(
        SketchValue,
        entities=tuple(
            Replace(Value, geometry=Profile) if Value.id == Selected else Value
            for Value in SketchValue.entities
        ),
    )
    with Pytest.raises(ValueError, match="center point disagrees"):
        _ = ApplyDepthEdit(
            Original,
            PlanValue[1].ParameterId,
            None,
            PlanValue[1].DistanceMm,
            Profile,
            Original.support_planes[0].transform,
            EditedSketch=Edited,
        )
