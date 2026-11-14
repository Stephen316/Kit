import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

KRootPath = FilePath(__file__).resolve().parents[2]
KReaderPath = KRootPath / "re/automation/FusionReader.py"
KManifestPath = KRootPath / "re/automation/Corpus.json"
KControlAsset = (
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)
KArchiveAsset = "re/Fusion/examples/.f3z/example1.f3z"


def RunFusionReader(
    ArgumentList: list[str], TimeLimit: int = 300
) -> Subprocess.CompletedProcess[str]:
    return Subprocess.run(
        [System.executable, str(KReaderPath), *ArgumentList],
        capture_output=True,
        text=True,
        timeout=TimeLimit,
        check=False,
    )


def ReadChunk(
    TargetPath: FilePath, AssetChunk: list[str]
) -> tuple[FilePath, Subprocess.CompletedProcess[str]]:
    ArgumentList = ["--allow-partial", "--output", str(TargetPath)]
    for AssetPath in AssetChunk:
        ArgumentList += ["--asset", AssetPath]
    return TargetPath, RunFusionReader(ArgumentList, TimeLimit=1200)


def FusionAssets() -> list[dict[str, str | int]]:
    Manifest = JsonCodec.loads(KManifestPath.read_text(encoding="utf-8"))
    return [
        Asset
        for Asset in Manifest["assets"]
        if Asset.get("kind") == "native" and Asset.get("format") in ("f3d", "f3z")
    ]
