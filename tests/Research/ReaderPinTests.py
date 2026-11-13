import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath


def CheckReadPins() -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Manifest = JsonCodec.loads((RootPath / "re/automation/Corpus.json").read_text())
    AssetPath = "re/solidworks/examples/.SLDPRT/example.SLDPRT"
    with TempFiles.TemporaryDirectory() as TempPath:
        TargetPath = FilePath(TempPath)
        PinFile = TargetPath / "Manifest.json"
        for FieldName, FieldData in (
            ("sha256", "0" * 64),
            ("git_blob", "0" * 40),
            ("prefix_hex", "00" * 16),
            ("size_bytes", 1),
            ("format", "sldasm"),
        ):
            Changed = JsonCodec.loads(JsonCodec.dumps(Manifest))
            for Asset in Changed["assets"]:
                if Asset["path"] == AssetPath:
                    Asset[FieldName] = FieldData
            _ = PinFile.write_text(JsonCodec.dumps(Changed), encoding="utf-8")
            OutputPath = TargetPath / FieldName
            ResultInfo = Subprocess.run(
                [
                    System.executable,
                    str(RootPath / "re/automation/SolidworksReader.py"),
                    "--manifest",
                    str(PinFile),
                    "--asset",
                    AssetPath,
                    "--output",
                    str(OutputPath),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            assert ResultInfo.returncode == 1, ResultInfo.stdout
            assert not OutputPath.exists()
            assert JsonCodec.loads(ResultInfo.stderr)["portable_complete"] is False
