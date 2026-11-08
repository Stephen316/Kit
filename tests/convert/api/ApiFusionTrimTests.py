# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from json import loads as LoadJson

import pytest as Pytest

from convert import open_document as OpenDocument
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
    Sample = next(Item for Item in Captured["samples"] if Item["file"] == Filename)
    (TruthBody,) = Sample["result_bodies"]
    Document = OpenDocument(Folder / Filename, strict=False)
    StepValue = Document.feature_timeline[-1]
    assert isinstance(StepValue.definition, DistanceExtrude)
    Portions = StepValue.attributes["fusion.profile_portions"]
    assert len(Portions) == Count and len({Item[3] for Item in Portions}) == Count
    (SketchValue,) = Document.sketches
    assert not SketchValue.closed_profile_entity_ids
    assert {Item[0] for Item in Portions} <= {
        Entity.id for Entity in SketchValue.entities
    }
    if Capture == "repeated_circle":
        assert len({Item[0] for Item in Portions}) == 3
        assert {(Item[3][4], Item[3][5]) for Item in Portions} == {
            (2, 4),
            (4, 4),
            (1, 2),
            (2, 2),
        }
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
            Face.same_sense for Face in Model.faces if Face.surface_id in Curved
        } == {False, True}
    Topology = BodyValue.topology
    assert Topology.volume == Pytest.approx(TruthBody["volume_cm3"] * 1000)
    Bounds = Topology.bounding_box
    assert Bounds is not None
    for Corner, Expected in zip(
        (Bounds.minimum, Bounds.maximum), TruthBody["bounds_cm"]
    ):
        assert (Corner.x, Corner.y, Corner.z) == Pytest.approx(
            tuple(Value * 10 for Value in Expected), abs=1e-8
        )
    assert Document.validate() == ()
    assert CadDocument.from_json(Document.to_json()) == Document
