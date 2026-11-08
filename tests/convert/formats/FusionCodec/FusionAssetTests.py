# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from dataclasses import replace as Replace
from io import BytesIO
from zipfile import ZipFile

import pytest as Pytest

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionArchive
from convert.formats.Fusion.AssetCodec.EmitAsset import EmitAsset
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.NativeHistory import ReadHistory
from convert.formats.Fusion.SourceProof.Auxiliary.ActiveRoute.ReadAssetRoutes import (
    ReadAssetRoutes,
)
from convert.formats.Fusion.SourceProof.Auxiliary.ReadAuxFrame import ReadAuxFrame
from tests.convert.api.ApiFusionAssemblyTests import KRequiresCodec
from tests.convert.formats.FusionCodec.AssetTestPlan import MakeAssetPlan


# the portable writer always emits a deterministic native zip directory
def TestAssetZip() -> None:
    Value = MakeAssetPlan()
    DataValue = EmitAsset(Value)
    assert EmitAsset(Value) == DataValue
    with ZipFile(BytesIO(DataValue)) as Archive:
        ZipRows = Archive.infolist()
        Files = tuple(Entry for Entry in ZipRows if not Entry.is_dir())
        assert len(Files) == 9
        assert [Entry.compress_type for Entry in Files] == [
            93,
            0,
            93,
            93,
            93,
            93,
            93,
            93,
            93,
        ]
        assert all(Entry.flag_bits == 0x800 for Entry in ZipRows)
        assert Archive.read("Properties.dat") == bytes(4)


# independent readers recover the generated timeline and active routing identities
@KRequiresCodec
def TestAssetRead() -> None:
    Value = MakeAssetPlan()
    with OpenFusionArchive(EmitAsset(Value)) as Archive:
        BulkData, Spans = Archive.ReadDesign()
        MetaData = Archive.ReadMember(
            "FusionAssetName[Active]/FusionDesignSegmentType1/MetaStream.dat", 4096
        )
        Owners = {
            SpanValue.ObjectId: SpanValue for SpanValue in Spans if SpanValue.IsPrimary
        }
        OwnerId, Entries, Groups = ReadHistory(BulkData, Owners[42], Owners)
        assert (OwnerId, Entries) == (40, (43, 41))
        assert Groups[0].GroupName == "Authored"
        ActFrame = ReadAuxFrame(Archive, SegmentKind.KAct)
        Route = ReadAssetRoutes(Archive, BulkData, MetaData, Spans, ActFrame)
        assert Route.Manifest.AssetId == Value.RootMeta.AssetId
        assert tuple(
            RowValue.Key for RowValue in Route.Routes if RowValue.IsResolved
        ) == ("1_2",)


# a broken cross segment relationship must fail before zip publication
def TestAssetGuards() -> None:
    Value = MakeAssetPlan()
    Browser = Value.Browser
    BadRoot = Replace(Browser.Records[1], Payload=bytes(77))
    BadFolder = Replace(Browser.Records[2], Payload=b"")
    Cases = (
        (
            Replace(
                Value,
                RootMeta=Replace(Value.RootMeta, AssetId=Value.AssetMeta.SnapshotId),
            ),
            "root manifest",
        ),
        (
            Replace(
                Value,
                AssetMeta=Replace(
                    Value.AssetMeta, SnapshotId=Value.AssetMeta.PhysicalGuid
                ),
            ),
            "snapshot",
        ),
        (Replace(Value, Browser=Value.Design), "manifest slot"),
        (
            Replace(
                Value,
                Browser=Replace(
                    Browser, Records=(Browser.Records[0], BadRoot, *Browser.Records[2:])
                ),
            ),
            "owner reference",
        ),
        (
            Replace(
                Value,
                Browser=Replace(
                    Browser,
                    Records=(*Browser.Records[:2], BadFolder, *Browser.Records[3:]),
                ),
            ),
            "folder role",
        ),
        (Replace(Value, EmptyConfig=True), "configuration pair"),
    )
    for Changed, Expected in Cases:
        with Pytest.raises(ValueError, match=Expected):
            EmitAsset(Changed)
