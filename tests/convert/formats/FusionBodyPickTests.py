# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt


from struct import pack as PackData

import pytest as Pytest

from convert.formats.Fusion.DesignZip import ReadDesignZip
from convert.formats.Fusion.SelectionProxy import (
    ReadSelectDesc,
    ReadSelectDescs,
    ReadSelectList,
)
from convert.formats.Fusion.Topology.BodyPick import ReadBodyPick
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec, KStudyPath

# distinct feature families share one explicit body descriptor layout
KBodyPickCases = (
    ("combinemodes-dcb4956eca6b/cut_multiple.f3d", 436, 437, ((440, 354, 358, 322),)),
    ("combinemodes-dcb4956eca6b/join_consume.f3d", 359, 360, ((363, 354, 358, 322),)),
    (
        "bodyselections-62e42366c722/scale_two_bodies_point.f3d",
        389,
        393,
        ((396, 275, 281, 243), (400, 354, 358, 322)),
    ),
    ("bodyselections-62e42366c722/shell_body.f3d", 282, 283, ((286, 275, 281, 243),)),
    (
        "bodyselections-62e42366c722/mirror_two_bodies_plane.f3d",
        381,
        389,
        ((392, 275, 281, 243), (396, 354, 358, 322)),
    ),
)


# each historical operand preserves body and source identity in authored proxy order
@KRequiresCodec
@Pytest.mark.parametrize("SampleName,FeatureId,ProxyId,Expected", KBodyPickCases)
def TestBodyPick(
    SampleName: str,
    FeatureId: int,
    ProxyId: int,
    Expected: tuple[tuple[int, int, int, int], ...],
) -> None:
    BulkData, Spans = ReadDesignZip((KStudyPath / SampleName).read_bytes())
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Descriptors, Attributes = ReadSelectList(BulkData, Owners, ProxyId, FeatureId)
    assert Descriptors == ReadSelectDescs(BulkData, Owners, ProxyId, FeatureId)
    Picks = tuple(
        ReadBodyPick(BulkData, Owners, Identity, FeatureId) for Identity in Descriptors
    )
    assert (
        tuple(
            (Value.DescriptorId, Value.BodyId, Value.AnchorId, Value.SourceId)
            for Value in Picks
        )
        == Expected
    )
    if SampleName.startswith("combinemodes"):
        assert Attributes == {
            "DcFeatureOperationIdFlag": 309 if FeatureId == 436 else 306
        }
        assert len(Picks[0].ContextIds) == 1
    else:
        assert Attributes == {}
        assert all(Value.ContextIds == () for Value in Picks)
    if len(Descriptors) == 1:
        assert ReadSelectDesc(BulkData, Owners, ProxyId, FeatureId) == Descriptors[0]
    else:
        with Pytest.raises(ValueError, match="proxy count"):
            _ = ReadSelectDesc(BulkData, Owners, ProxyId, FeatureId)


# duplicate or mismatched primary references cannot become an ordered operand list
@KRequiresCodec
def TestBodyProxy() -> None:
    SampleName, FeatureId, ProxyId, _ = KBodyPickCases[2]
    BulkData, Spans = ReadDesignZip((KStudyPath / SampleName).read_bytes())
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    Second = Owners[ProxyId].PayloadOffset + 4 + 6 + 11
    WrongIds = BulkData[: Second + 1] + PackData("<Q", 396) + BulkData[Second + 9 :]
    with Pytest.raises(ValueError, match="missing or repeated"):
        _ = ReadSelectDescs(WrongIds, Owners, ProxyId, FeatureId)
    with Pytest.raises(ValueError, match="proxy owner"):
        _ = ReadSelectList(BulkData, Owners, ProxyId, FeatureId + 1)


# descriptor support recipe and native context must remain mutually consistent
@KRequiresCodec
def TestBadBodyPick() -> None:
    SampleName, FeatureId, _, _ = KBodyPickCases[0]
    BulkData, Spans = ReadDesignZip((KStudyPath / SampleName).read_bytes())
    Owners = {Value.ObjectId: Value for Value in Spans if Value.IsPrimary}
    PickValue = ReadBodyPick(BulkData, Owners, 440, FeatureId)
    DescStart = Owners[440].PayloadOffset + 4
    SupportEnd = Owners[PickValue.SupportId].EndOffset
    RecipeEnd = Owners[PickValue.RecipeId].EndOffset
    BadValues = (
        (DescStart + 198, PackData("<Q", PickValue.BodyId), "typed Fusion selection"),
        (
            Owners[464].PayloadOffset + 6,
            PackData("<Q", 431),
            "context selects a different entity",
        ),
        (SupportEnd - 26, PackData("<Q", PickValue.RecipeId), "support ownership"),
        (RecipeEnd - 1, bytes(1), "whole body recipe"),
    )
    for Offset, Replacement, ErrorText in BadValues:
        Modified = (
            BulkData[:Offset] + Replacement + BulkData[Offset + len(Replacement) :]
        )
        with Pytest.raises(ValueError, match=ErrorText):
            _ = ReadBodyPick(Modified, Owners, 440, FeatureId)
    with Pytest.raises(ValueError, match="descriptor owner"):
        _ = ReadBodyPick(BulkData, Owners, 440, FeatureId + 1)
