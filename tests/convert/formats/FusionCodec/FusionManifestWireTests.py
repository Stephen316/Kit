# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt

from dataclasses import replace as Replace
from io import BytesIO
from pathlib import Path as FilePath
from struct import pack as PackValue
from sys import version_info as PythonVersion
from typing import cast as CastValue
from zipfile import ZipFile

from pytest import mark as TestMark, raises as Raises

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.SegmentCodec.Manifest.EmitAssetWire import EmitAssetWire
from convert.formats.Fusion.SegmentCodec.Manifest.EmitRootWire import EmitRootWire
from convert.formats.Fusion.SegmentCodec.Manifest.ManifestTypes import (
    AssetManifest,
    RootManifest,
)
from convert.formats.Fusion.SegmentCodec.Manifest.ReadAssetWire import ReadAssetWire
from convert.formats.Fusion.SegmentCodec.Manifest.ReadRootWire import ReadRootWire
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KActiveManifest,
    KMaxManifestBytes,
    KRootManifest,
    ReadActiveMeta,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadAssetMeta import (
    KAssetKeys,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadRootMeta import (
    KRootKeys,
)

# fixture paths resolve from the test checkout regardless of the working directory
KRepoRoot = FilePath(__file__).resolve().parents[4]

# saved native manifests use the standard library archive codec from the newer runtime
KRequiresCodec = TestMark.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

# fresh typed identities and words exercise authoring without a captured payload
KSyntheticRoot = RootManifest(
    "Workshop 🛠",
    "Dimensions\r\n\tCheck λ and 🔧",
    (
        "6a123456-1111-4222-8333-abcdef123456",
        "6b123456-1111-4222-8333-abcdef123456",
    ),
    ((1 << 32) - 1, 0),
    tuple((KeyName, Index + 70) for Index, KeyName in enumerate(KRootKeys)),
    "6c123456-1111-4222-8333-abcdef123456",
)

# the asset can share the fresh root identity while storing different native tokens
KSyntheticAsset = AssetManifest(
    KSyntheticRoot.AssetId,
    "6d123456-1111-4222-8333-abcdef123456",
    tuple((KeyName, Index + 90) for Index, KeyName in enumerate(KAssetKeys)),
    "6e123456-1111-4222-8333-abcdef123456",
    7,
)


# fresh bytes work through the independent archive and source proof reader
def TestFreshWire() -> None:
    RootBytes = EmitRootWire(KSyntheticRoot)
    AssetBytes = EmitAssetWire(KSyntheticAsset)
    assert ReadRootWire(RootBytes) == KSyntheticRoot
    assert ReadAssetWire(AssetBytes) == KSyntheticAsset
    Target = BytesIO()
    with ZipFile(Target, "w") as Archive:
        Archive.writestr(KRootManifest, RootBytes)
        Archive.writestr(KActiveManifest, AssetBytes)
    with OpenFusionZip(Target.getvalue()) as Archive:
        Manifest = ReadActiveMeta(Archive)
    assert Manifest.AssetId == KSyntheticRoot.AssetId
    assert Manifest.SnapshotId == KSyntheticAsset.SnapshotId
    assert Manifest.RootVersions == KSyntheticRoot.Versions
    assert Manifest.AssetVersions == KSyntheticAsset.Versions


# invalid typed document fields fail before any bytes reach the caller
@TestMark.parametrize(
    "Value",
    (
        Replace(KSyntheticRoot, AssetId=KSyntheticRoot.AssetId.upper()),
        Replace(
            KSyntheticRoot,
            OpaqueIds=CastValue(tuple[str, str], KSyntheticRoot.OpaqueIds[:1]),
        ),
        Replace(KSyntheticRoot, OpaqueWords=(0, 1 << 32)),
        Replace(KSyntheticRoot, Versions=KSyntheticRoot.Versions[::-1]),
        Replace(KSyntheticRoot, Title="Line\nbreak"),
        Replace(KSyntheticRoot, Description="Invalid\x00control"),
        Replace(KSyntheticRoot, Description="🔧" * 2049),
    ),
)
def TestBadRoot(Value: RootManifest) -> None:
    with Raises(ValueError):
        _ = EmitRootWire(Value)


# unsupported active values cannot emit contradictory manifest fields
@TestMark.parametrize(
    "Value",
    (
        Replace(KSyntheticAsset, SnapshotId="00000000-0000-0000-0000-000000000000"),
        Replace(KSyntheticAsset, PhysicalGuid="bad"),
        Replace(KSyntheticAsset, OpaqueWord=6),
        Replace(KSyntheticAsset, Versions=KSyntheticAsset.Versions[:-1]),
    ),
)
def TestBadAsset(Value: AssetManifest) -> None:
    with Raises(ValueError):
        _ = EmitAssetWire(Value)


# byte checks cover exact grammar without accepting unrelated fields or stream tails
def TestReadGuards() -> None:
    RootBytes = EmitRootWire(KSyntheticRoot)
    AssetBytes = EmitAssetWire(KSyntheticAsset)
    for Reader, Payload, Before, After in (
        (ReadRootWire, RootBytes, b"3-2-0-0", b"3-2-0-1"),
        (
            ReadRootWire,
            RootBytes,
            PackValue("<II", 1234, 20),
            PackValue("<II", 1234, 21),
        ),
        (ReadAssetWire, AssetBytes, b"physicalChangeGuid", b"physicalChangeVoid"),
        (ReadAssetWire, AssetBytes, b"FusionACTSegmentType", b"FusionCADSegmentType"),
    ):
        assert Before in Payload
        with Raises(ValueError):
            _ = Reader(Payload.replace(Before, After, 1))
        with Raises(ValueError, match="trailing data"):
            _ = Reader(Payload + b"\0")
        with Raises(ValueError, match="payload size"):
            _ = Reader(bytes(KMaxManifestBytes + 1))
        for Count in range(len(Payload)):
            with Raises(ValueError):
                _ = Reader(Payload[:Count])


# both saved header variants replay with their original typed opaque fields
@KRequiresCodec
@TestMark.parametrize(
    ("FileName", "OpaqueWords", "OpaqueWord"),
    (
        (
            "re/Fusion/Study/planedefinitions-6cd0820a832e/offset.f3d",
            (30, 709099584),
            5,
        ),
        ("examples/.f3d/example2.f3d", (36, 708837440), 7),
    ),
)
def TestWireReplay(
    FileName: str, OpaqueWords: tuple[int, int], OpaqueWord: int
) -> None:
    with ZipFile(KRepoRoot / FileName) as Archive:
        RootBytes = Archive.read(KRootManifest)
        AssetBytes = Archive.read(KActiveManifest)
    RootValue, AssetValue = ReadRootWire(RootBytes), ReadAssetWire(AssetBytes)
    assert RootValue.AssetId == AssetValue.AssetId
    assert RootValue.OpaqueWords == OpaqueWords
    assert AssetValue.OpaqueWord == OpaqueWord
    assert EmitRootWire(RootValue) == RootBytes
    assert EmitAssetWire(AssetValue) == AssetBytes
