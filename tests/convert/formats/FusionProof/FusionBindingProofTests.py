# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace

import pytest as Pytest

from convert import open_document as OpenDocument
from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.Extrudes.ExtrudeControl import ReadExtrudeHead
from convert.formats.Fusion.HistoryRef import ReadOptionalRef
from convert.formats.Fusion.MetaCursor import MetaCursor
from convert.formats.Fusion.NumericParam import ReadNativeNum
from convert.formats.Fusion.RecordSpan import RecordSpan
from convert.formats.Fusion.SourceProof.Bindings.ReadBindingProof import (
    ReadBindingProof,
)
from interchange.document.models.DocumentModel import CadDocument
from interchange.features.FeatureAngleRev import AngularRevolve
from interchange.features.FeatureBoundScale import BoundScale
from interchange.features.FeatureDistExt import DistanceExtrude
from interchange.features.FeaturePlaneExt import PlaneExtrude
from interchange.features.FeaturePlaneRev import PlaneRevolve
from interchange.records.RecordParameter import Parameter
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath


# proof uses a real projected owner and independent indexed bytes from the same control
def BindFixture(Sample: str) -> tuple[bytes, dict[int, RecordSpan], CadDocument]:
    Source = KStudyPath / Sample
    Bulk, Spans = ReadDesignZip(Source.read_bytes())
    return (
        Bulk,
        {Span.ObjectId: Span for Span in Spans if Span.IsPrimary},
        OpenDocument(Source, strict=False),
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
    return ParamValue.attributes["fusion.parameter_index"]


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
    Bulk, Owners, Document = BindFixture(Sample)
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
        Span = Owners[int(Origin.native_id)]
        Native = ReadNativeNum(Bulk[Span.PayloadOffset + 4 : Span.EndOffset])
        assert (
            ReadBindingProof(
                Bulk, Owners, Document, Native, Span, ParamValue, RankValue
            ).ObjectId
            == Native.BindingId
        )
        Actual += 1
    assert Actual == Expected


# equal numeric caches cannot substitute for the recorded owner control reference
@KRequiresCodec
def TestBindGuard() -> None:
    Bulk, Owners, Document = BindFixture("extents-f0f33a9a605f/distance_positive.f3d")
    Along, Taper = BoundParams(Document)
    assert Along.provenance is not None
    Span = Owners[int(Along.provenance.native_id)]
    Native = ReadNativeNum(Bulk[Span.PayloadOffset + 4 : Span.EndOffset])
    assert Native.BindingId is not None
    Binding = Owners[Native.BindingId]
    Header = Binding.PayloadOffset
    Body = Header + 4
    Book = Owners[int.from_bytes(Bulk[Body + 63 : Body + 71], "little")]
    StepValue = Document.feature_timeline[-1]
    assert StepValue.provenance is not None
    Owner = Owners[int(StepValue.provenance.native_id)]
    Control = MetaCursor(Bulk[Owner.PayloadOffset + 4 : Owner.EndOffset])
    ReadExtrudeHead(Control)
    ReadOptionalRef(Control)
    ReadOptionalRef(Control)
    AlongOffset = Owner.PayloadOffset + 4 + Control.Offset + 1
    EditData = bytearray(Bulk)
    EditData[AlongOffset : AlongOffset + 8] = Taper.attributes[
        "fusion.binding_id"
    ].to_bytes(8, "little")
    with Pytest.raises(ValueError, match="owner control slot"):
        ReadBindingProof(bytes(EditData), Owners, Document, Native, Span, Along, 1)
    for Offset in (
        Header,
        Body + 14,
        Body + 16,
        Body + 21,
        Body + 40,
        Body + 49,
        Body + 73,
        Book.PayloadOffset + 17,
    ):
        EditData = bytearray(Bulk)
        EditData[Offset] ^= 1
        with Pytest.raises(ValueError):
            ReadBindingProof(bytes(EditData), Owners, Document, Native, Span, Along, 1)
    with Pytest.raises(ValueError, match="parameter rank"):
        ReadBindingProof(Bulk, Owners, Document, Native, Span, Along, 2)
    Unsupported = Replace(
        Document,
        feature_timeline=(
            *Document.feature_timeline[:-1],
            Replace(StepValue, definition=None),
        ),
    )
    with Pytest.raises(ValueError, match="owner control route"):
        ReadBindingProof(Bulk, Owners, Unsupported, Native, Span, Along, 1)
    EditData = bytearray(Bulk)
    EditData[Book.PayloadOffset + 4 + 23] ^= 1
    assert (
        ReadBindingProof(bytes(EditData), Owners, Document, Native, Span, Along, 1)
        == Binding
    )
