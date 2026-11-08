# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from convert.formats.Fusion.SegmentCodec.Manifest.ManifestLayout import (
    KAssetName,
    KExportLabel,
    KRootFormat,
    KRootMagic,
    KWireVersion,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestSink import ManifestSink
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import RootManifest
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadRootMeta import KRootKeys


# a fresh typed document root can be packed without a captured manifest template
def EmitRootWire(Value: RootManifest) -> bytes:
    if (
        not isinstance(Value, RootManifest)
        or type(Value.OpaqueIds) is not tuple
        or len(Value.OpaqueIds) != 2
        or type(Value.OpaqueWords) is not tuple
        or len(Value.OpaqueWords) != 2
    ):
        raise ValueError("Invalid typed Fusion root manifest")
    SinkValue = ManifestSink()
    SinkValue.AddText(KRootFormat[0])
    SinkValue.AddText(KRootFormat[1])
    SinkValue.AddText(KRootFormat[2], WideText=True)
    SinkValue.AddText(Value.Title, WideText=True)
    SinkValue.AddDescription(Value.Description)
    for GuidText in Value.OpaqueIds:
        SinkValue.AddGuid(GuidText)
    SinkValue.AddWord(KRootMagic)
    SinkValue.AddWord(KWireVersion)
    for Number in Value.OpaqueWords:
        SinkValue.AddWord(Number)
    SinkValue.AddVersions(Value.Versions, KRootKeys)
    SinkValue.AddWord(0)
    SinkValue.AddBytes(b"\0")
    SinkValue.AddGuid(Value.AssetId)
    SinkValue.AddWord(1)
    SinkValue.AddText(KAssetName, WideText=True)
    SinkValue.AddWord(0)
    SinkValue.AddBytes(b"\1")
    SinkValue.AddText(KExportLabel, WideText=True)
    return bytes(SinkValue.Buffer)
