# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from tests.convert.api.InputCases import KInputCases
from typing import cast as CastValue
from io import BytesIO as ByteStream
from struct import pack as PackValue
from zipfile import ZipFile

import pytest as Pytest

from tests.convert.FusionRead import OpenResearch as OpenDocument
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# public reads and interchange retain scoped historic operands without current body paths
@KRequiresCodec
@Pytest.mark.parametrize("Sample,KindValue,Operation,KeepTools,Expected", KInputCases)
def TestBodyInputs(
    Sample: str,
    KindValue: FeatureKind,
    Operation: BooleanOp | None,
    KeepTools: bool | None,
    Expected: tuple[tuple[str, int, int], ...],
) -> None:
    Archive = KStudyPath / Sample
    Document = OpenDocument(Archive, StrictMode=False)
    StepValue = next(
        Value for Value in Document.feature_timeline if Value.kind == KindValue
    )
    assert StepValue.operation == Operation
    assert StepValue.attributes.get("fusion.combine.keep_tool_bodies") is KeepTools
    assert Capability.KSelections in Document.capabilities
    Selections = {Value.id: Value for Value in Document.selections}
    Picks = tuple(
        Selections[Identity]
        for Identity in StepValue.selection_ids
        if Selections[Identity].query.get("kind") == "historical_body"
    )
    assert (
        tuple(
            (
                PickValue.query["role"],
                PickValue.query["native_body_id"],
                PickValue.query["native_source_id"],
            )
            for PickValue in Picks
        )
        == Expected
    )
    for Ordinal, PickValue in enumerate(Picks):
        assert (
            PickValue.query["kind"] == "historical_body"
            and PickValue.query["ordinal"] == Ordinal
        )
        assert PickValue.path == () and PickValue.query["native_scope_id"] == 33
        assert PickValue.query["native_component_id"] == 3
        assert PickValue.provenance is not None
        assert PickValue.provenance.native_id == str(
            PickValue.attributes["fusion.descriptor_object_id"]
        )
        assert (
            PickValue.query["source_feature_id"]
            == f"fusion-feature-35-{Expected[Ordinal][2]}"
        )
    if KeepTools is False:
        Members = CastValue(
            dict[str, tuple[dict[str, object], ...]],
            Document.metadata["fusion.body_inventory"],
        )["members"]
        assert Expected[0][1] not in {Member["object_id"] for Member in Members}
    assert CadDocument.from_json(Document.to_json()) == Document
    Explicit = OpenDocument(
        Archive,
        StrictMode=False,
        Configuration=str(Document.metadata["fusion.history_id"]),
    )
    assert Explicit.selections == Document.selections


# a typed mirror association must name the historical anchor and not its body
@KRequiresCodec
def TestWrongBody() -> None:
    Archive = KStudyPath / KInputCases[-1][0]
    BulkData, Spans = ReadDesignZip(Archive.read_bytes())
    Terminal = next(
        Value for Value in Spans if Value.IsPrimary and Value.ObjectId == 483
    )
    Offset = Terminal.PayloadOffset + 6
    assert BulkData[Offset : Offset + 8] == PackValue("<Q", 281)
    Wrong = BulkData[:Offset] + PackValue("<Q", 275) + BulkData[Offset + 8 :]
    Stream = ByteStream()
    with ZipFile(Archive) as Original, ZipFile(Stream, "w") as Mutated:
        Mutated.writestr(KDesignPrefix + "BulkStream.dat", Wrong)
        MetaName = KDesignPrefix + "MetaStream.dat"
        Mutated.writestr(MetaName, Original.read(MetaName))
    _ = Stream.seek(0)
    Document = OpenDocument(Stream, StrictMode=False)
    StepValue = Document.feature_timeline[-1]
    assert StepValue.kind == FeatureKind.KNative and not StepValue.selection_ids
    assert any(
        Issue.entity_id == StepValue.id
        and "context selects a different entity" in Issue.message
        for Issue in Document.diagnostics
    )


# face and occurrence operands cannot silently turn into local historical whole bodies
@KRequiresCodec
@Pytest.mark.parametrize(
    "Sample,Identity",
    (
        ("bodyselections-62e42366c722/shell_two_faces.f3d", 282),
        ("combinemodes-dcb4956eca6b/join_component.f3d", 422),
    ),
)
def TestBodyOmitted(Sample: str, Identity: int) -> None:
    Document = OpenDocument(KStudyPath / Sample, StrictMode=False)
    StepValue = next(
        Value
        for Value in Document.feature_timeline
        if Value.id == f"fusion-feature-35-{Identity}"
    )
    assert StepValue.kind == FeatureKind.KNative and not StepValue.selection_ids
    assert any(
        Issue.entity_id == StepValue.id
        and Issue.code == "fusion.body_inputs.unsupported"
        for Issue in Document.diagnostics
    )
