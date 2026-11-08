# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.AssetCodec.AssetPlan import AssetPlan
from convert.formats.Fusion.AssetCodec.BuildSegFrame import BuildSegFrame
from convert.formats.Fusion.AssetCodec.CheckAssetAct import CheckAssetAct
from convert.formats.Fusion.AssetCodec.CheckAssetBrow import CheckAssetBrow
from convert.formats.Fusion.AssetCodec.MakeAssetRows import MakeAssetRows
from convert.formats.Fusion.AssetCodec.ReadConfigFiles import ReadConfigFiles
from convert.formats.Fusion.AssetCodec.Zip.EmitAssetZip import EmitAssetZip
from convert.formats.Fusion.MetaIndex import SegmentKind
from convert.formats.Fusion.SegmentCodec.Manifest.EmitAssetWire import EmitAssetWire
from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire


# publish the core archive only after all native segment and manifest links agree
def EmitAsset(Value: AssetPlan) -> bytes:
    if not isinstance(Value, AssetPlan) or type(Value.EmptyConfig) is not bool:
        raise ValueError("Expected a typed Fusion asset plan")
    RootData = EmitRootWire(Value.RootMeta)
    AssetData = EmitAssetWire(Value.AssetMeta)
    if Value.RootMeta.AssetId != Value.AssetMeta.AssetId:
        raise ValueError("Fusion root manifest disagrees with active asset")
    Design = BuildSegFrame(Value.Design, SegmentKind.KDesign, 0)
    ActFrame = BuildSegFrame(Value.ActPlan, SegmentKind.KAct, 1)
    Browser = BuildSegFrame(Value.Browser, SegmentKind.KBrowser, 2)
    CheckAssetAct(Design, ActFrame, Value.AssetMeta.SnapshotId)
    CheckAssetBrow(Design, Browser)
    ConfigFiles = ReadConfigFiles(Design, Value.EmptyConfig)
    return EmitAssetZip(
        MakeAssetRows(RootData, AssetData, (Design, ActFrame, Browser), ConfigFiles)
    )
