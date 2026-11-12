from io import BytesIO
from pathlib import Path as FilePath
from struct import pack as PackData
from sys import version_info as PythonVersion
from zipfile import ZipFile

from pytest import mark as TestMarks, raises as Raises

from convert.formats.Fusion.ArchiveRead.IndexedArchive import OpenFusionZip
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ActiveManifest import (
    ActiveManifest,
)
from convert.formats.Fusion.SourceProof.Auxiliary.Manifest.ReadActiveMeta import (
    KActiveManifest,
    KMaxManifestBytes,
    KRootManifest,
    ReadActiveMeta,
)

# saved captures use the native archive codec from the newer runtime
KRequiresCodec = TestMarks.skipif(
    PythonVersion < (3, 14), reason="native Fusion fixture requires ZIP Zstandard"
)

# a single controlled asset supplies both a base snapshot and an independently saved edit
KCaptureFolder = (
    FilePath(__file__).resolve().parents[4]
    / "re"
    / "Fusion"
    / "Study"
    / "output-7230965e9265"
)

# this independent capture uses the alternate observed manifest header words
KExampleFile = (
    FilePath(__file__).resolve().parents[4] / "examples" / ".f3d" / "example2.f3d"
)


# extract the native members needed to test the relationship without design records
def CaptureMembers(Source: FilePath) -> dict[str, bytes]:
    with ZipFile(Source) as Capture:
        return {
            NameValue: Capture.read(NameValue)
            for NameValue in (KRootManifest, KActiveManifest)
        }


# controlled archives preserve valid framing while exercising member failures
def ManifestZip(Members: dict[str, bytes]) -> bytes:
    Target = BytesIO()
    with ZipFile(Target, "w") as Archive:
        for NameValue, DataValue in Members.items():
            Archive.writestr(NameValue, DataValue)
        Archive.writestr("unrelated.dat", b"")
    return Target.getvalue()


# the same asset can legitimately have multiple distinct native snapshot identities
@KRequiresCodec
def TestAssetRevs() -> None:
    Results: list[ActiveManifest] = []
    for FileName in ("depth07_a.f3d", "depth13.f3d"):
        Capture = ManifestZip(CaptureMembers(KCaptureFolder / FileName))
        with OpenFusionZip(Capture) as Archive:
            Result = ReadActiveMeta(Archive)
            assert (Result.RootMember, Result.ActiveMember) == Archive.Members[:2]
            assert Archive.ReadNames == frozenset((KRootManifest, KActiveManifest))
            assert Result.RootVersions[:2] == (("Application", 1), ("CAM", 4))
            assert Result.AssetVersions == (
                ("Application", 139),
                ("ParaMesh", 13),
                ("Server", 36),
                ("VolField", 4),
            )
            Results.append(Result)
    assert Results[0].AssetId == Results[1].AssetId
    assert Results[0].SnapshotId != Results[1].SnapshotId


# the independent capture shares the schema despite different header words
@KRequiresCodec
def TestMetaVariant() -> None:
    with OpenFusionZip(KExampleFile.read_bytes()) as Archive:
        Result = ReadActiveMeta(Archive)
        assert Result.AssetId == "952d0a7d-2d52-48d3-8596-400ac4f0bc0b"
        assert Result.SnapshotId == "9cf7970e-6238-4119-befb-55fb5432c805"
        assert Archive.ReadNames == frozenset((KRootManifest, KActiveManifest))


# structurally valid manifests copied between distinct assets cannot establish a join
@KRequiresCodec
def TestForeignMeta() -> None:
    Members = CaptureMembers(KCaptureFolder / "depth07_a.f3d")
    Members[KActiveManifest] = CaptureMembers(KExampleFile)[KActiveManifest]
    with OpenFusionZip(ManifestZip(Members)) as Archive:
        with Raises(ValueError, match="asset IDs disagree"):
            _ = ReadActiveMeta(Archive)


# aliases and oversized members fail before the proof inflates either exact path
def TestMetaBounds() -> None:
    Members = {KRootManifest: b"root", KActiveManifest: b"active"}
    for Changed in (
        {KRootManifest: Members[KRootManifest], "Other/" + KActiveManifest: b"x"},
        {KRootManifest: b"", KActiveManifest: Members[KActiveManifest]},
        {**Members, KActiveManifest: bytes(KMaxManifestBytes + 1)},
        {KRootManifest: Members[KRootManifest], KActiveManifest + "/": b""},
    ):
        with OpenFusionZip(ManifestZip(Changed)) as Archive:
            with Raises(ValueError, match="Missing or oversized"):
                _ = ReadActiveMeta(Archive)
            assert Archive.ReadNames == frozenset()


# framing and exact schema keys protect both manifest readers from misleading payloads
@KRequiresCodec
@TestMarks.parametrize(
    ("NameValue", "Before", "After"),
    (
        (KRootManifest, b"3-2-0-0", b"3-2-0-1"),
        (KRootManifest, PackData("<II", 1234, 20), PackData("<II", 1234, 21)),
        (KRootManifest, b"SimCommon", b"simCommon"),
        (
            KRootManifest,
            "NA_EXPORT".encode("utf-16le"),
            "\x00A_EXPORT".encode("utf-16le"),
        ),
        (KActiveManifest, b"physicalChangeGuid", b"physicalChangeVoid"),
        (KActiveManifest, b"FusionACTSegmentType", b"FusionCADSegmentType"),
        (KActiveManifest, PackData("<I", 36), PackData("<I", 0xFFFFFFFF)),
    ),
)
def TestMetaSchema(NameValue: str, Before: bytes, After: bytes) -> None:
    Members = CaptureMembers(KCaptureFolder / "depth07_a.f3d")
    assert Before in Members[NameValue]
    Members[NameValue] = Members[NameValue].replace(Before, After, 1)
    with OpenFusionZip(ManifestZip(Members)) as Archive:
        with Raises(ValueError):
            _ = ReadActiveMeta(Archive)


# extension bytes and truncated fields cannot masquerade as a completely parsed schema
@KRequiresCodec
def TestMetaExtent() -> None:
    Members = CaptureMembers(KCaptureFolder / "depth07_a.f3d")
    for NameValue in (KRootManifest, KActiveManifest):
        for Changed in (Members[NameValue][:-1], Members[NameValue] + b"\x00"):
            with OpenFusionZip(ManifestZip({**Members, NameValue: Changed})) as Archive:
                with Raises(ValueError):
                    _ = ReadActiveMeta(Archive)
