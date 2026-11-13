import hashlib as Hashlib
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


class ReaderClient:
    def __init__(self, TargetPath: FilePath) -> None:
        super().__init__()
        self.TargetPath = TargetPath
        self.ScriptPath = (
            FilePath(__file__).resolve().parents[2]
            / "re/automation/SolidworksReader.py"
        )

    def ReadAsset(self, AssetPath: str) -> tuple[str, Subprocess.CompletedProcess[str]]:
        OutputPath = self.TargetPath / Hashlib.sha256(AssetPath.encode()).hexdigest()
        return AssetPath, Subprocess.run(
            [
                System.executable,
                str(self.ScriptPath),
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
