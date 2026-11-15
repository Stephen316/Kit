from json import dumps as DumpJson, loads as LoadJson
from pathlib import Path as FilePath

from pytest import mark as TestMark

from tests.CliResearch.ResearchAssets import KArchiveAsset, KControlAsset, KSwAsset
from tests.CliResearch.ResearchClient import ResearchCli
from tests.CliResearch.ResearchRoot import ResearchRoot


# a changed corpus identity must prevent reader publication before any output appears
@TestMark.parametrize(
    "FieldName,FieldValue",
    (
        ("sha256", "0" * 64),
        ("git_blob", "0" * 40),
        ("size_bytes", 1),
        ("prefix_hex", "00" * 16),
    ),
)
def CheckPinFailure(FieldName: str, FieldValue: str | int, TmpPath: FilePath) -> None:
    Manifest = LoadJson((ResearchRoot() / "re/automation/Corpus.json").read_bytes())
    for Entry in Manifest["assets"]:
        if Entry["path"] == KSwAsset:
            Entry[FieldName] = FieldValue
    ManifestPath = TmpPath / "Manifest.json"
    _ = ManifestPath.write_text(DumpJson(Manifest))
    TargetPath = TmpPath / "Rejected"
    Result = ResearchCli(
        TmpPath,
        "solidworks",
        "--asset",
        KSwAsset,
        "--manifest",
        str(ManifestPath),
        "--output",
        str(TargetPath),
    )
    assert Result.returncode == 1 and not TargetPath.exists()


# one invalid archive pin must prevent publication of every asset in its batch
def CheckBatchPins(TmpPath: FilePath) -> None:
    Manifest = LoadJson((ResearchRoot() / "re/automation/Corpus.json").read_bytes())
    for Entry in Manifest["assets"]:
        if Entry["path"] == KArchiveAsset:
            Entry["sha256"] = "0" * 64
    ManifestPath = TmpPath / "Manifest.json"
    _ = ManifestPath.write_text(DumpJson(Manifest))
    TargetPath = TmpPath / "Rejected"
    Result = ResearchCli(
        TmpPath,
        "fusion",
        "--asset",
        KControlAsset,
        "--asset",
        KArchiveAsset,
        "--manifest",
        str(ManifestPath),
        "--output",
        str(TargetPath),
    )
    assert Result.returncode == 1 and not TargetPath.exists()
    assert not list(TmpPath.glob(".fusion-reader-*"))
