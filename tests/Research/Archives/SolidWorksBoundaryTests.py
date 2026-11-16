from pathlib import Path as FilePath
from struct import pack as PackBytes, unpack_from as UnpackFrom

import pytest as Pytest

from convert.adapters.solidworks import build_sldprt as BuildSldprt
from convert.adapters.solidworks.Container.Container import (
    SldprtArchive,
    container_signatures as ContainerSignatures,
)
from convert.adapters.solidworks.Container.Parasolid import (
    decode_brep_model as DecodeBrep,
)
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart
from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentModel import CadDocument

# each corruption control keeps the original observed discovery data named explicitly
KCaptureRoot = FilePath(__file__).resolve().parents[3] / "re/automation/PairedCaptures"

# the rotated sketch has a different valid choice of principal datum
KPlaneFile = KCaptureRoot / "P01/solidworks-75b9308cf13e/P01-solidworks-plane-yz.SLDPRT"

# the supported boss provides an independent later failure after its profile closes
KBossFile = (
    KCaptureRoot / "P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT"
)

# the active solid and its decodable profile packet coexist in this saved cut
KCutFile = KCaptureRoot / "P04/solidworks-c1986308375a/P04-solidworks-baseline-a.SLDPRT"

# stream labels identify the selected configuration and its independent feature packets
KPartStream = "Contents/Config-0-Partition"

# the native resolved stream carries the profile and operation ownership records
KFeatureStream = "Contents/Config-0-ResolvedFeatures"


# test inputs change one native field while keeping the same envelope and other stream bytes
def RebuildPart(
    Original: bytes, Archive: SldprtArchive, Streams: dict[str, bytes]
) -> bytes:
    return BuildSldprt(
        Streams,
        file_id=Archive.file_id,
        format_version=Archive.format_version,
        signatures=ContainerSignatures(Original),
    )


# a mutation must verify the exact valid native value before substituting the alternative
def PatchSwInt(BlobValue: bytes, Offset: int, Previous: int, NextValue: int) -> bytes:
    assert UnpackFrom("<i", BlobValue, Offset) == (Previous,)
    return BlobValue[:Offset] + PackBytes("<i", NextValue) + BlobValue[Offset + 4 :]


# archive reads in these controls use the normal public document boundary
def ReadSwFixture(RawValue: bytes, IncludeBrep: bool = False) -> CadDocument:
    return OpenDocument(
        RawValue,
        SourceFormat="solidworks.sldprt",
        IncludeTess=False,
        IncludeBrep=IncludeBrep,
        StrictMode=False,
    )


# a valid principal datum with the wrong frame must withhold the typed attachment
def TestSwPlaneRef() -> None:
    Original = KPlaneFile.read_bytes()
    Archive = SldprtArchive.from_bytes(Original)
    (Before,) = ReadSwFixture(Original).sketches
    assert Before.attributes["support_plane_source"] == "typed-archive-reference"
    assert Before.provenance is not None
    (Support,) = tuple(
        Value
        for Value in Before.provenance.spans
        if Value.record_kind == "sketch-support-reference"
    )
    Streams = Archive.streams
    assert (Support.stream, Support.length) == (KFeatureStream, 4)
    Streams[Support.stream] = PatchSwInt(Streams[Support.stream], Support.offset, 4, 2)
    (After,) = ReadSwFixture(RebuildPart(Original, Archive, Streams)).sketches
    assert After.id == Before.id and After.provenance is not None
    assert After.attributes["support_plane_source"] != "typed-archive-reference"
    assert all(
        Value.record_kind != "sketch-support-reference"
        for Value in After.provenance.spans
    )


# the same viewer must keep the closed rectangle while refusing the unsupported boss selector
def TestSwBossGuard() -> None:
    Original = KBossFile.read_bytes()
    Archive = SldprtArchive.from_bytes(Original)
    Resolved = Archive.require(KFeatureStream)
    Parsed = ReadRectPart(Archive.require("Contents/Config-0"), Resolved, 19000)
    assert Parsed.Boss is not None
    Selector = Parsed.Boss["choosers"]["end"]
    assert UnpackFrom("<H3i", Resolved, Selector) == (0, 0, 0, 1)
    Streams = Archive.streams
    Streams[KFeatureStream] = PatchSwInt(Resolved, Selector + 10, 1, 0)
    Updated = ReadSwFixture(RebuildPart(Original, Archive, Streams))
    (SketchValue,) = Updated.sketches
    assert SketchValue.attributes["support_plane_source"] == "typed-archive-reference"
    assert len(SketchValue.closed_profile_entity_ids[0]) == 4
    (BossStep,) = tuple(
        Value for Value in Updated.feature_timeline if Value.name == "BlindBoss"
    )
    assert BossStep.provenance is not None
    assert all(
        Value.record_kind != "extrusion-end-spec" for Value in BossStep.provenance.spans
    )


# a valid opposing cap must not attach the cut while the reached rectangle still qualifies
def TestSwCapOwner() -> None:
    Original = KCutFile.read_bytes()
    Archive = SldprtArchive.from_bytes(Original)
    Nominal = ReadSwFixture(Original)
    (FacePick,) = tuple(
        Value
        for Value in Nominal.selections
        if Value.query.get("kind") == "historical_face_occurrence"
    )
    assert FacePick.provenance is not None
    (CapSpan,) = tuple(
        Value
        for Value in FacePick.provenance.spans
        if Value.record_kind == "cut-face-cap"
    )
    assert CapSpan.stream == KFeatureStream
    Streams = Archive.streams
    Streams[CapSpan.stream] = PatchSwInt(
        Streams[CapSpan.stream], CapSpan.offset + CapSpan.length - 8, 1, 0
    )
    Updated = ReadSwFixture(RebuildPart(Original, Archive, Streams))
    AssertCutRefuse(Updated)


# an unresolved cut attachment must keep the independently bound rectangle and equations
def AssertCutRefuse(Document: CadDocument) -> None:
    Sketches = {Value.name: Value for Value in Document.sketches}
    assert (
        Sketches["RectangleSketch"].attributes["support_plane_source"]
        == "typed-archive-reference"
    )
    assert (
        Sketches["CutSketch"].attributes["support_plane_source"] != "typed-archive-face"
    )
    assert not Sketches["CutSketch"].closed_profile_entity_ids
    assert all(
        Value.query.get("kind") != "historical_face_occurrence"
        for Value in Document.selections
    )
    (CutStep,) = tuple(
        Value for Value in Document.feature_timeline if Value.name == "BlindCut"
    )
    assert CutStep.provenance is not None
    assert all(
        Value.record_kind != "cut-target-body" for Value in CutStep.provenance.spans
    )
    (Offset,) = tuple(
        Value for Value in Document.parameters if Value.name == "cut_left_mm"
    )
    assert Offset.provenance is not None
    assert any(
        Value.record_kind == "equation-target-slot" for Value in Offset.provenance.spans
    )


# the wrapper and stream presence controls retain the intended selected partition failure
def BreakPartMut(Streams: dict[str, bytes], Scenario: str) -> None:
    if Scenario == "unsupported":
        Streams[KPartStream] = Streams["Contents/Config-0-GhostPartition"]
    elif Scenario == "truncated":
        Streams[KPartStream] = Streams[KPartStream][:24]
    else:
        _ = Streams.pop(KPartStream)


# a readable profile packet is evidence for a cache rather than the selected design body
@Pytest.mark.parametrize("Scenario", ("unsupported", "truncated", "missing"))
def TestSwPartGuard(Scenario: str) -> None:
    Original = KCutFile.read_bytes()
    Archive = SldprtArchive.from_bytes(Original)
    Streams = Archive.streams
    BreakPartMut(Streams, Scenario)
    Updated = ReadSwFixture(RebuildPart(Original, Archive, Streams), IncludeBrep=True)
    assert Updated.brep is None
    (BodyValue,) = Updated.bodies
    assert "parasolid_active_payload_id" not in BodyValue.attributes
    (Embedded,) = tuple(
        Value
        for Value in Updated.brep_payloads
        if Value.source_stream == KFeatureStream
    )
    assert Embedded.data is not None
    Profile = DecodeBrep(Embedded.data)
    assert Profile is not None and len(Profile.faces) == 1
    Selected = tuple(
        Value for Value in Updated.brep_payloads if Value.source_stream == KPartStream
    )
    if Scenario == "unsupported":
        (Retained,) = Selected
        assert (
            Retained.kind == "partition"
            and Retained.data is not None
            and DecodeBrep(Retained.data) is None
        )
    else:
        assert not Selected
    Diagnostics = tuple(
        Value
        for Value in Updated.diagnostics
        if Value.code == "sldprt.parasolid_decode_failed"
        and Value.attributes.get("stream") == KPartStream
    )
    assert len(Diagnostics) == int(Scenario == "truncated")
    (CutSketch,) = tuple(
        Value for Value in Updated.sketches if Value.name == "CutSketch"
    )
    assert CutSketch.attributes["support_plane_source"] == "typed-archive-face"
