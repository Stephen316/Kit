import json as JsonCodec
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath

# corpus commands must resolve repository paths consistently from any test working directory
KRootPath = FilePath(__file__).resolve().parents[2]

# all reader scenarios need the same executable entry point to reflect actual intake behavior
KReaderPath = KRootPath / "re/automation/FusionReader.py"

# provenance scenarios use the production corpus manifest as the authority for input selection
KManifestPath = KRootPath / "re/automation/Corpus.json"

# native control checks need a previously proven ordinary rectangle to anchor expected results
KControlAsset = (
    "re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d"
)

# archive rejection needs a real assembly input distinct from the supported part control
KArchiveAsset = "re/Fusion/examples/.f3z/example1.f3z"


# shared subprocess policy keeps timeout and diagnostics consistent across fusion reader scenarios
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


# large inventories need bounded reads so coverage remains attributable to each submitted chunk
def ReadChunk(
    TargetPath: FilePath, AssetChunk: list[str]
) -> tuple[FilePath, Subprocess.CompletedProcess[str]]:
    ArgumentList = ["--allow-partial", "--output", str(TargetPath)]
    for AssetPath in AssetChunk:
        ArgumentList += ["--asset", AssetPath]
    return TargetPath, RunFusionReader(ArgumentList, TimeLimit=1200)


# the census must use the declared fusion inventory to avoid counting undeclared application inputs
def FusionAssets() -> list[dict[str, str | int]]:
    Manifest = JsonCodec.loads(KManifestPath.read_text(encoding="utf-8"))
    return [
        Asset
        for Asset in Manifest["assets"]
        if Asset.get("kind") == "native" and Asset.get("format") in ("f3d", "f3z")
    ]
