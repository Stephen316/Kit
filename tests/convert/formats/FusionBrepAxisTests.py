# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO
from math import radians as Radians
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# the native controls select the bottom rim of the prior extrusion along different axes
KEdgeAxisCases = (
    (
        "revolveaxes-a83b542c4a07/brep_edge.f3d",
        (0.0, 30.0, 0.0),
        (0.0, 1.0, 0.0),
        750.0,
        "prism-edge-2",
    ),
    (
        "revolveaxes-14700158dba9/brep_edge_offset_x.f3d",
        (48.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        1110.0,
        "prism-edge-3",
    ),
)


# typed body and edge selection must retain the native source and both neutral solids
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Capture", "Origin", "Direction", "SeedVolume", "EdgeName"), KEdgeAxisCases
)
def TestBrepAxisRev(
    Capture: str,
    Origin: tuple[float, ...],
    Direction: tuple[float, ...],
    SeedVolume: float,
    EdgeName: str,
) -> None:
    DocValue = OpenDocument(KStudyPath / Capture, strict=False)
    _, Creator, _, Sweep = DocValue.feature_timeline
    Definition = Sweep.definition
    assert isinstance(Definition, AngularRevolve)
    Base = Definition.AxisOrigin
    Axis = Definition.AxisDirection
    assert (Base.x, Base.y, Base.z) == Pytest.approx(Origin)
    assert (Axis.x, Axis.y, Axis.z) == Pytest.approx(Direction)
    assert Creator.id in Sweep.input_feature_ids
    assert DocValue.parameter(Definition.AlongParameterId).value.value == Pytest.approx(
        Radians(73)
    )
    Seed, Result = DocValue.bodies
    assert Seed.final_feature_id == Creator.id and Result.final_feature_id == Sweep.id
    assert Seed.provenance is not None and Result.provenance is not None
    assert Seed.provenance.native_id == "275" and Result.provenance.native_id == "378"
    assert Seed.topology is not None and Result.topology is not None
    assert [Value.topology.volume for Value in (Seed, Result)] == Pytest.approx(
        (SeedVolume, 2446.25347959525)
    )
    (Selection,) = DocValue.selections
    assert Selection.id == Definition.AxisSelectionId == "fusion-selection-347-axis"
    assert (
        Selection.path[0].entity_kind == "body"
        and Selection.path[0].entity_id == Seed.id
    )
    assert Selection.path[1].entity_kind == "edge"
    assert Selection.path[1].entity_id == f"{Seed.id}-{EdgeName}"
    assert DocValue.brep is not None
    assert any(Value.id == Selection.path[1].entity_id for Value in DocValue.brep.edges)
    assert Selection.provenance is not None
    assert any(Span.record_kind == "asm_history" for Span in Selection.provenance.spans)
    assert not DocValue.brep.validate(frozenset({Seed.id, Result.id}))
    assert CadDocument.FromJson(DocValue.ToJson()) == DocValue


# a valid saved line cannot rescue a recipe naming the wrong native face
@KRequiresCodec
def TestBrepAxisName() -> None:
    Source = KStudyPath / KEdgeAxisCases[0][0]
    BulkData, Spans = ReadDesignZip(Source.read_bytes())
    Recipe = next(Value for Value in Spans if Value.IsPrimary and Value.ObjectId == 353)
    Position = Recipe.PayloadOffset + 4 + 22
    Changed = bytearray(BulkData)
    assert Changed[Position] == ord("3")
    Changed[Position] = ord("1")
    Buffer = BytesIO()
    with ZipFile(Source) as Archive, ZipFile(Buffer, "w") as Copy:
        for NameValue in Archive.namelist():
            Copy.writestr(
                NameValue,
                (
                    Changed
                    if NameValue == KDesignPrefix + "BulkStream.dat"
                    else Archive.read(NameValue)
                ),
            )
    DocValue = OpenDocument(Buffer.getvalue(), strict=False)
    assert DocValue.feature_timeline[-1].definition is None
    assert DocValue.brep is None
    assert any(
        Value.code == "fusion.revolve.angular_extent_unsupported"
        for Value in DocValue.diagnostics
    )
