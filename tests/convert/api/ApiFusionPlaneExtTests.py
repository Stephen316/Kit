# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace
from math import pi as CirclePi

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.PlaneExtValues import GetPlaneExt
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# saved fusion bounds corroborate editable plane selection and closed solid geometry
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "RoleName", "Bounds", "NativeId"),
    (
        ("to_plane", "end", (0, 30), "293"),
        ("to_plane_offset", "end", (0, 34), "293"),
        ("from_plane", "start", (35, 52), "296"),
    ),
)
def CheckPlaneExt(
    Capture: str, RoleName: str, Bounds: tuple[float, float], NativeId: str
) -> None:
    Archive = KStudyPath / "extents-f0f33a9a605f" / f"{Capture}.f3d"
    Document = OpenDocument(Archive, StrictMode=False)
    StepValue = Document.feature_timeline[-1]
    Definition = StepValue.definition
    assert isinstance(Definition, PlaneExtrude) and Definition.LimitRole == RoleName
    assert (Definition.LengthParameterId is not None) == (RoleName == "start")
    Parameters = {Param.id: Param for Param in Document.parameters}
    Selections = {PickValue.id: PickValue for PickValue in Document.selections}
    Frames = {Frame.id: Frame for Frame in Document.support_planes}
    Sketches = {SketchValue.id: SketchValue for SketchValue in Document.sketches}
    PickValue = Selections[Definition.PlaneSelectionId]
    assert PickValue.path[0].entity_id == "fusion-plane-234"
    assert "fusion-feature-35-235" in StepValue.input_feature_ids
    Values = GetPlaneExt(
        StepValue, Definition, Parameters, Selections, Frames, Sketches
    )
    assert (Values.LowerMm, Values.UpperMm) == Pytest.approx(Bounds)
    AssertPlaneBrep(Document, Bounds, NativeId)
    Offset = Parameters[Definition.OffsetParameterId]
    Parameters[Offset.id] = Replace(
        Offset, value=Replace(Offset.value, value=float(Offset.value.value) + 0.2)
    )
    Edited = GetPlaneExt(
        StepValue, Definition, Parameters, Selections, Frames, Sketches
    )
    assert Edited.UpperMm == Pytest.approx(Bounds[1] + 2)
    assert Edited.LowerMm == Pytest.approx(
        Bounds[0] + (2 if RoleName == "start" else 0)
    )
    assert CadDocument.from_json(Document.to_json()) == Document


# rebuilt plane extrusion topology and measures must match the selected bounds
def AssertPlaneBrep(
    Document: CadDocument, Bounds: tuple[float, float], NativeId: str
) -> None:
    (BodyValue,) = Document.bodies
    assert (
        BodyValue.provenance is not None and BodyValue.provenance.native_id == NativeId
    )
    assert Document.brep is not None and Document.brep.shells[0].closed
    Topology = BodyValue.topology
    assert (Topology.face_count, Topology.edge_count, Topology.vertex_count) == (
        3,
        2,
        2,
    )
    assert Topology.volume == Pytest.approx(CirclePi * 100 * (Bounds[1] - Bounds[0]))
    BoxValue = Topology.bounding_box
    assert BoxValue is not None
    assert (BoxValue.minimum.z, BoxValue.maximum.z) == Pytest.approx(Bounds)
