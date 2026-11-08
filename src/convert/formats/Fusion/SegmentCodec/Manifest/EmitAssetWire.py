# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetKind,
    KAssetName,
    KAssetRole,
    KOpaqueWords,
    KPhysicalKey,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import AssetManifest
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
    KAssetSegments,
)


# known ordered segment rows and counts are derived from the manifest grammar
def EmitAssetWire(Value: AssetManifest) -> bytes:
    if not isinstance(Value, AssetManifest) or (
        type(Value.OpaqueWord) is not int or Value.OpaqueWord not in KOpaqueWords
    ):
        raise ValueError("Invalid typed Fusion active manifest")
    SinkValue = ManifestSink()
    SinkValue.AddText(KAssetName, WideText=True)
    SinkValue.AddGuid(Value.AssetId)
    SinkValue.AddGuid(Value.SnapshotId)
    SinkValue.AddText(KAssetRole)
    SinkValue.AddWord(KWireVersion)
    SinkValue.AddVersions(Value.Versions, KAssetKeys)
    SinkValue.AddText(KAssetKind)
    SinkValue.AddWord(0)
    SinkValue.AddBytes(b"\0")
    SinkValue.AddWord(1)
    SinkValue.AddText(KPhysicalKey)
    SinkValue.AddGuid(Value.PhysicalGuid)
    SinkValue.AddWord(0)
    SinkValue.AddWord(Value.OpaqueWord)
    SinkValue.AddCount(KAssetSegments, len(KAssetSegments))
    for Index, Segment in enumerate(KAssetSegments):
        SinkValue.AddWord(Index)
        SinkValue.AddText(Segment.value)
        SinkValue.AddText(Segment.value)
    return bytes(SinkValue.Buffer)
