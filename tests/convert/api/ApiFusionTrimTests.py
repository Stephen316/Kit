# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from typing import cast as CastValue
from json import loads as LoadJson

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from interchange.brep.surfaces.BrepSurfaces import CylinderSurface
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureDistExt import DistanceExtrude
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# saved volumes and bounds check distinct profile families through the public reader
@KRequiresCodec
@Pytest.mark.parametrize(
    ("FolderName", "Capture", "Count"),
    (
        ("trimselectorholdouts-ac245ecd1e2f", "repeated_circle", 4),
        ("trimmedprofiles-a804f8da1496", "circle_right_complement", 2),
        ("placedprofiletrims-037ed41056a4", "origin_xz_mixed_segment", 2),
        ("placedprofiletrims-037ed41056a4", "angled_rectangle_overlap", 4),
    ),
)
def CheckTrimSolid(FolderName: str, Capture: str, Count: int) -> None:
    Folder = KStudyPath / FolderName
    Filename = f"{Capture}.f3d"
    Captured = LoadJson((Folder / "ground_truth.json").read_text(encoding="utf-8"))
    Sample = next(
        ItemValue for ItemValue in Captured["samples"] if ItemValue["file"] == Filename
    )
    (TruthBody,) = Sample["result_bodies"]
    Document = OpenDocument(Folder / Filename, StrictMode=False)
    StepValue = Document.feature_timeline[-1]
    assert isinstance(StepValue.definition, DistanceExtrude)
    Portions = CastValue(
        tuple[tuple[str, float, float, tuple[int, ...]], ...],
        StepValue.attributes["fusion.profile_portions"],
    )
    assert (
        len(Portions) == Count
        and len({ItemValue[3] for ItemValue in Portions}) == Count
    )
    (SketchValue,) = Document.sketches
    assert not SketchValue.closed_profile_entity_ids
    assert {ItemValue[0] for ItemValue in Portions} <= {
        Entity.id for Entity in SketchValue.entities
    }
    if Capture == "repeated_circle":
        assert len({ItemValue[0] for ItemValue in Portions}) == 3
        assert {(ItemValue[3][4], ItemValue[3][5]) for ItemValue in Portions} == {
            (2, 4),
            (4, 4),
            (1, 2),
            (2, 2),
        }
    AssertTrimShape(
        Document, Capture, Count, TruthBody["volume_cm3"], TruthBody["bounds_cm"]
    )
    AssertTrimRound(Document)


# trimmed solids must match captured topology volume and bounds
def AssertTrimShape(
    Document: CadDocument,
    Capture: str,
    Count: int,
    VolumeCm: float,
    BoundsCm: list[list[float]],
) -> None:
    (BodyValue,) = Document.bodies
    Model = Document.brep
    assert Model is not None and Model.shells[0].closed
    assert (len(Model.faces), len(Model.edges), len(Model.vertices)) == (
        Count + 2,
        3 * Count,
        2 * Count,
    )
    if Capture == "circle_right_complement":
        Curved = {
            Surface.id
            for Surface in Model.surfaces
            if isinstance(Surface, CylinderSurface)
        }
        assert {
            FaceValue.same_sense
            for FaceValue in Model.faces
            if FaceValue.surface_id in Curved
        } == {False, True}
    Topology = BodyValue.topology
    assert Topology.volume == Pytest.approx(VolumeCm * 1000)
    Bounds = Topology.bounding_box
    assert Bounds is not None
    for Corner, Expected in zip((Bounds.minimum, Bounds.maximum), BoundsCm):
        assert (Corner.x, Corner.y, Corner.z) == Pytest.approx(
            tuple(Value * 10 for Value in Expected), abs=1e-8
        )


# trimmed profile provenance must survive neutral validation and serialization
def AssertTrimRound(Document: CadDocument) -> None:
    assert Document.validate() == ()
    assert CadDocument.from_json(Document.to_json()) == Document
