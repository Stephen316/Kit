from interchange.Features.FeatureStep import FeatureStep
from convert.Formats.Fusion.NativeParam import NativeParam
from dataclasses import replace as Replace

from typing import cast as CastValue

import pytest as Pytest

from tests.Convert.FusionRead import OpenResearch as OpenDocument
from convert.Formats.Fusion.DesignZip import ReadDesignZip
from convert.Formats.Fusion.Extrudes.ExtrudeControl import ReadExtrudeHead
from convert.Formats.Fusion.HistoryRef import ReadOptRefMut
from convert.Formats.Fusion.MetaCursor import MetaCursor
from convert.Formats.Fusion.NumericParam import ReadNativeNum
from convert.Formats.Fusion.RecordSpan import RecordSpan
from convert.Formats.Fusion.SourceProof.Bindings.ReadBindingProof import (
    ReadBindProof,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve
from interchange.Features.FeatureBoundScale import BoundScale
from interchange.Features.FeatureDistExt import DistanceExtrude
from interchange.Features.FeaturePlaneExt import PlaneExtrude
from interchange.Features.FeaturePlaneRev import PlaneRevolve
from interchange.Records.RecordParameter import Parameter
from tests.Convert.Api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# proof uses a real projected owner and independent indexed bytes from the same control
def BindFixture(Sample: str) -> tuple[bytes, dict[int, RecordSpan], CadDocument]:
    Source = KStudyPath / Sample
    BulkData, Spans = ReadDesignZip(Source.read_bytes())
    return (
        BulkData,
        {SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary},
        OpenDocument(Source, StrictMode=False),
    )


# model binding ranks exclude user parameters even when user indices precede them
def BoundParams(Document: CadDocument) -> tuple[Parameter, ...]:
    return tuple(
        sorted(
            (
                Value
                for Value in Document.parameters
                if Value.attributes["fusion.binding_id"] is not None
            ),
            key=ParamIndex,
        )
    )


# the native numeric index is independent of neutral tuple order
def ParamIndex(ParamValue: Parameter) -> int:
    IndexValue = ParamValue.attributes["fusion.parameter_index"]
    assert type(IndexValue) is int
    return IndexValue


# typed owner controls vary independently of the common numeric binding bytes
@KRequiresCodec
@Pytest.mark.parametrize(
    ("Sample", "Expected"),
    (
        ("extents-f0f33a9a605f/distance_positive.f3d", 2),
        ("holdouts-f8c508a73323/expression_depth.f3d", 2),
        ("models-b8a640dbddc6/two_sided.f3d", 4),
        ("models-b8a640dbddc6/symmetric_full.f3d", 2),
        ("extents-f0f33a9a605f/from_plane.f3d", 3),
        ("extents-f0f33a9a605f/to_plane_offset.f3d", 2),
        ("revolvemodes-8eb734486235/two_sided.f3d", 2),
        ("revolveto-b1d196f65c46/two_planes.f3d", 1),
        ("bodymodes-df9b7113539f/scale_nonuniform.f3d", 5),
        ("tools-fda3948848f4/Scale.f3d", 3),
    ),
)
def TestBindProof(Sample: str, Expected: int) -> None:
    BulkData, Owners, Document = BindFixture(Sample)
    StepIds = {
        Value.id
        for Value in Document.feature_timeline
        if isinstance(
            Value.definition,
            (DistanceExtrude, PlaneExtrude, AngularRevolve, PlaneRevolve, BoundScale),
        )
    }
    Actual = 0
    for RankValue, ParamValue in enumerate(BoundParams(Document), 1):
        if ParamValue.owner_id not in StepIds:
            continue
        Origin = ParamValue.provenance
        assert Origin is not None
        SpanValue = Owners[int(Origin.native_id)]
        Native = ReadNativeNum(
            BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset]
        )
        assert (
            ReadBindProof(
                BulkData, Owners, Document, Native, SpanValue, ParamValue, RankValue
            ).ObjectId
            == Native.BindingId
        )
        Actual += 1
    assert Actual == Expected


# equal numeric caches cannot substitute for the recorded owner control reference
@KRequiresCodec
def TestBindGuard() -> None:
    BulkData, Owners, Document = BindFixture(
        "extents-f0f33a9a605f/distance_positive.f3d"
    )
    Along, Taper = BoundParams(Document)
    assert Along.provenance is not None
    SpanValue = Owners[int(Along.provenance.native_id)]
    Native = ReadNativeNum(BulkData[SpanValue.PayloadOffset + 4 : SpanValue.EndOffset])
    assert Native.BindingId is not None
    Binding = Owners[Native.BindingId]
    Header = Binding.PayloadOffset
    BodyValue = Header + 4
    Workbook = Owners[
        int.from_bytes(BulkData[BodyValue + 63 : BodyValue + 71], "little")
    ]
    StepValue = Document.feature_timeline[-1]
    assert StepValue.provenance is not None
    Owner = Owners[int(StepValue.provenance.native_id)]
    Control = MetaCursor(BulkData[Owner.PayloadOffset + 4 : Owner.EndOffset])
    _ = ReadExtrudeHead(Control)
    _ = ReadOptRefMut(Control)
    _ = ReadOptRefMut(Control)
    AlongOffset = Owner.PayloadOffset + 4 + Control.Offset + 1
    EditData = bytearray(BulkData)
    EditData[AlongOffset : AlongOffset + 8] = CastValue(
        int, Taper.attributes["fusion.binding_id"]
    ).to_bytes(8, "little")
    with Pytest.raises(ValueError, match="owner control slot"):
        _ = ReadBindProof(
            bytes(EditData), Owners, Document, Native, SpanValue, Along, 1
        )
    AssertWireFlips(
        BulkData,
        Owners,
        Document,
        Native,
        SpanValue,
        Along,
        Header,
        BodyValue,
        Workbook,
    )
    AssertBindRoute(BulkData, Owners, Document, Native, SpanValue, Along, StepValue)
    EditData = bytearray(BulkData)
    EditData[Workbook.PayloadOffset + 4 + 23] ^= 1
    assert (
        ReadBindProof(bytes(EditData), Owners, Document, Native, SpanValue, Along, 1)
        == Binding
    )


# source owner routing and parameter rank are validated separately from the record layout
def AssertBindRoute(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Document: CadDocument,
    Native: NativeParam,
    SpanValue: RecordSpan,
    Along: Parameter,
    StepValue: FeatureStep,
) -> None:
    with Pytest.raises(ValueError, match="parameter rank"):
        _ = ReadBindProof(BulkData, Owners, Document, Native, SpanValue, Along, 2)
    Unsupported = Replace(
        Document,
        feature_timeline=(
            *Document.feature_timeline[:-1],
            Replace(StepValue, definition=None),
        ),
    )
    with Pytest.raises(ValueError, match="owner control route"):
        _ = ReadBindProof(BulkData, Owners, Unsupported, Native, SpanValue, Along, 1)


# the binding verifier must reject mutations to every required native witness
def AssertWireFlips(
    BulkData: bytes,
    Owners: dict[int, RecordSpan],
    Document: CadDocument,
    Native: NativeParam,
    SpanValue: RecordSpan,
    Along: Parameter,
    Header: int,
    BodyValue: int,
    Workbook: RecordSpan,
) -> None:
    for Offset in (
        Header,
        BodyValue + 14,
        BodyValue + 16,
        BodyValue + 21,
        BodyValue + 40,
        BodyValue + 49,
        BodyValue + 73,
        Workbook.PayloadOffset + 17,
    ):
        EditData = bytearray(BulkData)
        EditData[Offset] ^= 1
        with Pytest.raises(ValueError):
            _ = ReadBindProof(
                bytes(EditData), Owners, Document, Native, SpanValue, Along, 1
            )
