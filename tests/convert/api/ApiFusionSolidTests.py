# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from math import hypot as Hypot, pi as Pi

import pytest as Pytest

from convert import open_document as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# saved circular bounds corroborate caps and exact analytic lateral geometry
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "UpperRadius"),
    (("distance_positive", 10.0), ("taper", 12.087337535349378)),
)
def CheckCircleBody(Capture: str, UpperRadius: float) -> None:
    Archive = KStudyPath / "extents-f0f33a9a605f" / f"{Capture}.f3d"
    Document = OpenDocument(Archive, strict=False)
    (BodyValue,) = Document.bodies
    assert Document.brep is not None
    assert {Capability.KBodyStructure, Capability.KBrep} <= Document.capabilities
    assert Document.brep.bodies[0].design_body_id == BodyValue.id
    assert BodyValue.final_feature_id == Document.feature_timeline[-1].id
    Topology = BodyValue.topology
    assert (Topology.face_count, Topology.edge_count, Topology.vertex_count) == (
        3,
        2,
        2,
    )
    assert Topology.volume == Pytest.approx(
        Pi * 17 * (100 + 10 * UpperRadius + UpperRadius**2) / 3
    )
    assert Topology.surface_area == Pytest.approx(
        Pi * (100 + UpperRadius**2 + (10 + UpperRadius) * Hypot(17, UpperRadius - 10))
    )
    Bounds = Topology.bounding_box
    assert Bounds is not None
    assert (Bounds.minimum.x, Bounds.minimum.y, Bounds.minimum.z) == Pytest.approx(
        (-UpperRadius, -UpperRadius, 0)
    )
    assert (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z) == Pytest.approx(
        (UpperRadius, UpperRadius, 17)
    )
    assert CadDocument.from_json(Document.to_json()) == Document


# the straight rectangle oracle establishes a closed prism with all six planar faces
@KRequiresCodec
def CheckPrismBody() -> None:
    Archive = (
        KStudyPath / "thinextrudes-c1632bcb5efe" / "ordinary_rectangle_control.f3d"
    )
    Document = OpenDocument(Archive, strict=False)
    (BodyValue,) = Document.bodies
    Topology = BodyValue.topology
    assert Document.brep is not None and Document.brep.shells[0].closed
    assert (Topology.face_count, Topology.edge_count, Topology.vertex_count) == (
        6,
        12,
        8,
    )
    assert Topology.volume == Pytest.approx(30000)
    assert Topology.surface_area == Pytest.approx(5900)
    Bounds = Topology.bounding_box
    assert Bounds is not None
    assert (Bounds.minimum.x, Bounds.minimum.y, Bounds.minimum.z) == Pytest.approx(
        (0, 0, 0)
    )
    assert (Bounds.maximum.x, Bounds.maximum.y, Bounds.maximum.z) == Pytest.approx(
        (40, 30, 25)
    )
    assert Document.validate() == ()


# historical anchors of inactive results must not inflate the saved solid inventory
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "NativeIds"), (("suppressed_b", {260, 386}), ("rolled_back", {260}))
)
def CheckSavedSolid(Capture: str, NativeIds: set[int]) -> None:
    Archive = KStudyPath / "timeline-5867579925b5" / f"{Capture}.f3d"
    Document = OpenDocument(Archive, strict=False)
    assert Document.brep is not None and len(Document.brep.bodies) == len(NativeIds)
    assert {
        int(BodyValue.provenance.native_id)
        for BodyValue in Document.bodies
        if BodyValue.provenance
    } == NativeIds
    assert {
        Member["design_body_id"]
        for Member in Document.metadata["fusion.body_inventory"]["members"]
    } == {BodyValue.id for BodyValue in Document.bodies}


# live modifiers may change saved shapes while leaving their original creator anchors
@KRequiresCodec
def CheckSolidGuard() -> None:
    Archive = KStudyPath / "combinemodes-dcb4956eca6b" / "join_keep.f3d"
    Document = OpenDocument(Archive, strict=False)
    assert Document.brep is None and Document.bodies == ()
    assert len(Document.metadata["fusion.body_inventory"]["members"]) == 2
    assert any(
        Item.code == "fusion.extrude.body_unsupported" for Item in Document.diagnostics
    )
