from __future__ import annotations
import hashlib as Hashlib
import json as JsonLib
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
from pathlib import Path as FilePath
from os import environ as HostEnv
from typing import TypeGuard
import pytest as Pytest
from convert.Security.PathBoundary import ResolveTemp
from convert.adapters.solidworks.Container.Container import (
    Container as ContainerSignatures,
    DEFAULT_FILE_ID as IdInfo,
    DEFAULT_SIGNATURES as Signatures,
    SldprtArchive,
    build_sldprt as BuildSldprt,
)

# centralizes shared evidence so every related assertion uses one value
KEntries = 1000

# centralizes shared evidence so every related assertion uses one value
KSuffixes = frozenset({".SLDPRT", ".SLDASM"})

# centralizes shared evidence so every related assertion uses one value
KRootInfo = FilePath(__file__).resolve().parents[4]

# centralizes shared evidence so every related assertion uses one value
KExamples = KRootInfo / "re" / "solidworks" / "examples"

# centralizes shared evidence so every related assertion uses one value
KManifest = KRootInfo / "re" / "binaries" / "Manifest.json"

# centralizes shared evidence so every related assertion uses one value
KProvenance = KRootInfo / "re" / "data" / "Serialization" / "SignatureTable.json"

# centralizes shared evidence so every related assertion uses one value
KNameInfo = "sldmfcu.dll"

# centralizes shared evidence so every related assertion uses one value
KOffset = 5663808

# centralizes shared evidence so every related assertion uses one value
KRowInfo = ("64d80045", "ae0d4ef6", "54ce179a")

# centralizes shared evidence so every related assertion uses one value
KIndex = 711


# licensed oracle bytes stay outside the checkout and inside the temporary filesystem boundary
def LoadHostDll() -> bytes | None:
    InputPath = HostEnv.get("KIT_SOLIDWORKS_DLL")
    if InputPath is None:
        return None
    assert InputPath, "KIT_SOLIDWORKS_DLL must name an external licensed module"
    TargetPath = ResolveTemp(InputPath).resolve(strict=True)
    assert not TargetPath.is_relative_to(KRootInfo), TargetPath
    HostData = TargetPath.read_bytes()
    assert Hashlib.sha256(HostData).hexdigest() == RecordedHD()
    return HostData


# compatibility subprocesses prove oracle inputs respect containment before validating their identity
@Pytest.mark.parametrize("ProbeKind", ["outside", "symlink", "digest"])
def TestOraclePaths(TmpPath: FilePath, ProbeKind: str) -> None:
    OutsidePath = (
        FilePath(FilePath(Tempfile.gettempdir()).anchor) / "KitOracleOutside.dll"
    )
    InputPath = OutsidePath
    ExpectedText = "path escapes trusted root"
    if ProbeKind == "symlink":
        InputPath = TmpPath / "LinkedOracle.dll"
        InputPath.symlink_to(OutsidePath)
    elif ProbeKind == "digest":
        InputPath = TmpPath / "UnlicensedOracle.dll"
        _ = InputPath.write_bytes(b"kit oracle input boundary fixture\n")
        ExpectedText = "assert Hashlib.sha256(HostData).hexdigest() == RecordedHD()"
    EnvValues = dict(HostEnv)
    _ = EnvValues.pop("PYTEST_ADDOPTS", None)
    EnvValues["KIT_SOLIDWORKS_DLL"] = str(InputPath)
    ResultInfo = Subprocess.run(
        [
            System.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            f"{__file__}::TestTCRIAGROTVT",
        ],
        cwd=KRootInfo,
        capture_output=True,
        text=True,
        check=False,
        env=EnvValues,
        timeout=60,
    )
    assert ResultInfo.returncode == 1, ResultInfo.stdout + ResultInfo.stderr
    assert ExpectedText in ResultInfo.stdout, ResultInfo.stdout + ResultInfo.stderr


# keeps this focused behavior isolated so regressions remain immediately visible
def ExampleD() -> list[FilePath]:
    if not KExamples.is_dir():
        return []
    return sorted(
        (
            TargetPath
            for TargetPath in KExamples.rglob("*")
            if TargetPath.is_file() and TargetPath.suffix.upper() in KSuffixes
        )
    )


# keeps this focused behavior isolated so regressions remain immediately visible
def HostRows(BlobInfo: bytes) -> list[tuple[int, tuple[str, str, str]]]:
    SigBase = KOffset + KEntries * 4
    RowsInfo: list[tuple[int, tuple[str, str, str]]] = []
    for Index in range(KEntries):
        HeadInfo = KOffset + 4 * Index
        FileId = int.from_bytes(BlobInfo[HeadInfo : HeadInfo + 4], "big")
        Magics = (
            bytes(
                reversed(BlobInfo[SigBase + 12 * Index : SigBase + 12 * Index + 4])
            ).hex(),
            bytes(
                reversed(BlobInfo[SigBase + 12 * Index + 4 : SigBase + 12 * Index + 8])
            ).hex(),
            bytes(
                reversed(BlobInfo[SigBase + 12 * Index + 8 : SigBase + 12 * Index + 12])
            ).hex(),
        )
        RowsInfo.append((FileId, Magics))
    return RowsInfo


# recorded signature facts keep container validation reproducible when licensed vendor modules are unavailable
def RecordedRows() -> list[tuple[int, tuple[str, str, str]]]:
    RecordInfo = JsonLib.loads(KProvenance.read_text(encoding="utf-8"))
    return [
        (
            int(Entry["file_id"], 16),
            (Entry["local"], Entry["central"], Entry["end"]),
        )
        for Entry in RecordInfo["entries"]
    ]


# keeps external data bounded before content assertions
def IsObjectMap(Value: object) -> TypeGuard[dict[object, object]]:
    return isinstance(Value, dict)


# keeps external data bounded before content assertions
def IsObjectList(Value: object) -> TypeGuard[list[object]]:
    return isinstance(Value, list)


# keeps this focused behavior isolated so regressions remain immediately visible
def RecordedHD() -> str:
    Payload: object = JsonLib.loads(KManifest.read_text(encoding="utf-8"))
    if not IsObjectMap(Payload):
        raise AssertionError(f"{KManifest} must contain an object")
    Entries: object = Payload.get("binaries")
    if not IsObjectList(Entries):
        raise AssertionError(f"{KManifest} must contain binary entries")
    for Entry in Entries:
        if not IsObjectMap(Entry):
            continue
        NameValue: object = Entry.get("name")
        DigestValue: object = Entry.get("sha256")
        if NameValue == KNameInfo and isinstance(DigestValue, str):
            return DigestValue
    raise AssertionError(f"{KNameInfo} is absent from {KManifest}")


# keeps this focused behavior isolated so regressions remain immediately visible
def TestOOSRICIS() -> None:
    assert len(Signatures) == 3
    assert all((len(ItemValue) == 4 for ItemValue in Signatures))
    assert tuple((ItemValue.hex() for ItemValue in Signatures)) == KRowInfo
    assert 0 < IdInfo <= 4294967295
    Carried = 4 + sum((len(ItemValue) for ItemValue in Signatures))
    assert Carried == 16


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTCRIAGROTVT() -> None:
    RowsInfo = RecordedRows()
    HostInfo = LoadHostDll()
    if HostInfo is not None:
        assert HostRows(HostInfo) == RowsInfo
    assert len(RowsInfo) == KEntries
    assert len({FileId for FileId, _ in RowsInfo}) == KEntries
    assert RowsInfo[KIndex] == (IdInfo, KRowInfo)
    Matches = [
        Index
        for Index, (FileId, Magics) in enumerate(RowsInfo)
        if FileId == IdInfo and Magics == KRowInfo
    ]
    assert Matches == [KIndex]


# keeps this focused behavior isolated so regressions remain immediately visible
def TestPRDTWTATCR() -> None:
    RecordInfo = JsonLib.loads(KProvenance.read_text(encoding="utf-8"))
    assert RecordInfo["host"] == KNameInfo
    assert RecordInfo["host_sha256"] == RecordedHD()
    assert RecordInfo["block_file_offset"] == KOffset
    assert RecordInfo["entry_count"] == KEntries
    assert RecordInfo["shipped_rows"] == 1
    Entries = RecordInfo["entries"]
    assert len(Entries) == KEntries
    Carried = Entries[KIndex]
    assert Carried["file_id"] == f"{IdInfo:08x}"
    assert (Carried["local"], Carried["central"], Carried["end"]) == KRowInfo


# keeps this focused behavior isolated so regressions remain immediately visible
def TestGCUTCR() -> None:
    Streams = {
        "Contents/SolidWorks": b"<swSolidWorks/>",
        "Contents/Config-0-Partition": b"PS\x00\x00body",
    }
    BlobInfo = BuildSldprt(Streams)
    assert BlobInfo[:4] == IdInfo.to_bytes(4, "big")
    Archive = SldprtArchive.from_bytes(BlobInfo)
    assert Archive.file_id == IdInfo
    assert Archive.streams == Streams
    SignaturesA = ContainerSignatures(BlobInfo)
    assert SignaturesA == Signatures


# keeps this focused behavior isolated so regressions remain immediately visible
def TestEDPTOIWTOS() -> None:
    Documents = ExampleD()
    assert Documents
    HostRowsA = dict(RecordedRows())
    Covered = 0
    for TargetPath in Documents:
        BlobInfo = TargetPath.read_bytes()
        Archive = SldprtArchive.from_bytes(BlobInfo, TargetPath)
        SignaturesA = ContainerSignatures(BlobInfo)
        assert Archive.file_id in HostRowsA, TargetPath.name
        Recorded = HostRowsA[Archive.file_id]
        assert (
            tuple((ItemValue.hex() for ItemValue in SignaturesA)) == Recorded
        ), TargetPath.name
        Covered += 1
    assert Covered == len(Documents)


# keeps this focused behavior isolated so regressions remain immediately visible
def TestTPPADIWAST() -> None:
    Documents = ExampleD()
    assert Documents
    Template = Documents[0].read_bytes()
    SourceDoc = SldprtArchive.from_bytes(Template, Documents[0])
    assert SourceDoc.file_id != IdInfo or len(Documents) > 1
    Rebuilt = BuildSldprt(SourceDoc.streams, template=Template)
    Archive = SldprtArchive.from_bytes(Rebuilt)
    assert Archive.file_id == SourceDoc.file_id
    Expected = ContainerSignatures(Template)
    Actual = ContainerSignatures(Rebuilt)
    assert Actual == Expected
