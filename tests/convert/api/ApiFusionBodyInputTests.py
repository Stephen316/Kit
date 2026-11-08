# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from io import BytesIO as ByteStream
from struct import pack as PackValue
from zipfile import ZipFile

import pytest as Pytest

from convert import open_document as OpenDocument
from convert.formats.Fusion.DesignZip import KDesignPrefix, ReadDesignZip
from interchange.document.models.DocumentModel import CadDocument
from interchange.enums.EnumDocument import Capability
from interchange.enums.EnumFeatures import BooleanOp, FeatureKind
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# saved contrasts distinguish input order from body inventory and creator order
KInputCases = (
    (
        "combinemodes-dcb4956eca6b/cut_multiple.f3d",
        FeatureKind.KBoolean,
        BooleanOp.KCutOperation,
        True,
        (("tool", 354, 322), ("tool", 431, 399), ("target", 275, 243)),
    ),
    (
        "combinemodes-dcb4956eca6b/cut_swapped.f3d",
        FeatureKind.KBoolean,
        BooleanOp.KCutOperation,
        True,
        (("tool", 275, 243), ("target", 354, 322)),
    ),
    (
        "moretools-380212ab6368/CombineCutNoKeep.f3d",
        FeatureKind.KBoolean,
        BooleanOp.KCutOperation,
        False,
        (("tool", 324, 298), ("target", 260, 234)),
    ),
    (
        "bodyselections-62e42366c722/scale_two_bodies_point.f3d",
        FeatureKind.KScale,
        None,
        None,
        (("input", 275, 243), ("input", 354, 322)),
    ),
    (
        "scaleshellinputs-97ef1cfd19e4/shell_two_bodies.f3d",
        FeatureKind.KShell,
        None,
        None,
        (("input", 354, 322), ("input", 275, 243)),
    ),
    (
        "bodyselections-62e42366c722/mirror_two_bodies_plane.f3d",
        FeatureKind.KMirror,
        None,
        None,
        (("input", 275, 243), ("input", 354, 322)),
    ),
)


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
    Document = OpenDocument(Archive, strict=False)
    StepValue = next(
        Value for Value in Document.feature_timeline if Value.kind == KindValue
    )
    assert StepValue.operation == Operation
    assert StepValue.attributes.get("fusion.combine.keep_tool_bodies") is KeepTools
    assert Capability.KSelections in Document.capabilities
    Selections = {Value.id: Value for Value in Document.selections}
    Picks = tuple(Selections[Identity] for Identity in StepValue.selection_ids)
    assert (
        tuple(
            (
                Pick.query["role"],
                Pick.query["native_body_id"],
                Pick.query["native_source_id"],
            )
            for Pick in Picks
        )
        == Expected
    )
    for Ordinal, Pick in enumerate(Picks):
        assert (
            Pick.query["kind"] == "historical_body" and Pick.query["ordinal"] == Ordinal
        )
        assert Pick.path == () and Pick.query["native_scope_id"] == 33
        assert Pick.query["native_component_id"] == 3
        assert Pick.provenance is not None
        assert Pick.provenance.native_id == str(
            Pick.attributes["fusion.descriptor_object_id"]
        )
        assert (
            Pick.query["source_feature_id"]
            == f"fusion-feature-35-{Expected[Ordinal][2]}"
        )
    if KeepTools is False:
        Members = Document.metadata["fusion.body_inventory"]["members"]
        assert Expected[0][1] not in {Member["object_id"] for Member in Members}
    assert CadDocument.from_json(Document.to_json()) == Document
    Explicit = OpenDocument(
        Archive, strict=False, configuration=str(Document.metadata["fusion.history_id"])
    )
    assert Explicit.selections == Document.selections


# a typed mirror association must name the historical anchor and not its body
@KRequiresCodec
def TestBodyMismatch() -> None:
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
    Stream.seek(0)
    Document = OpenDocument(Stream, strict=False)
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
    Document = OpenDocument(KStudyPath / Sample, strict=False)
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
