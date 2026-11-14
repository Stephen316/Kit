import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.FusionClient import KControlAsset, KManifestPath, RunFusionReader


def CheckFusionPins() -> None:
    Manifest = JsonCodec.loads(KManifestPath.read_text(encoding="utf-8"))
    with TempFiles.TemporaryDirectory() as TempPath:
        TargetPath = FilePath(TempPath)
        PinFile = TargetPath / "Manifest.json"
        for FieldName, FieldData in (
            ("sha256", "0" * 64),
            ("git_blob", "0" * 40),
            ("prefix_hex", "00" * 16),
            ("size_bytes", 1),
            ("format", "sldprt"),
        ):
            Changed = JsonCodec.loads(JsonCodec.dumps(Manifest))
            for Asset in Changed["assets"]:
                if Asset["path"] == KControlAsset:
                    Asset[FieldName] = FieldData
            _ = PinFile.write_text(JsonCodec.dumps(Changed), encoding="utf-8")
            OutputPath = TargetPath / FieldName
            ResultInfo = RunFusionReader(
                [
                    "--manifest",
                    str(PinFile),
                    "--asset",
                    KControlAsset,
                    "--output",
                    str(OutputPath),
                ]
            )
            assert ResultInfo.returncode == 1, ResultInfo.stdout
            assert not OutputPath.exists()
            assert JsonCodec.loads(ResultInfo.stderr)["portable_complete"] is False


def CheckSelection() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        TargetPath = FilePath(TempPath)
        for CaseName, AssetList in (
            ("duplicate", [KControlAsset, KControlAsset]),
            ("unpinned", ["re/Fusion/Study/missing/unpinned.f3d"]),
            ("escaping", ["../outside.f3d"]),
        ):
            OutputPath = TargetPath / CaseName
            ArgumentList = ["--output", str(OutputPath)]
            for AssetPath in AssetList:
                ArgumentList += ["--asset", AssetPath]
            ResultInfo = RunFusionReader(ArgumentList)
            assert ResultInfo.returncode == 1, ResultInfo.stdout
            assert not OutputPath.exists()
            assert JsonCodec.loads(ResultInfo.stderr)["portable_complete"] is False
