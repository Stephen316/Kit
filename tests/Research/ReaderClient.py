import hashlib as Hashlib
import subprocess as Subprocess
import sys as System
from pathlib import Path as FilePath


# solidworks corpus checks need uniform subprocess custody for outcomes across many individual assets
class ReaderClient:

    # a shared destination keeps per asset reports within the private corpus run
    def __init__(self, TargetPath: FilePath) -> None:
        super().__init__()
        self.TargetPath = TargetPath
        self.ScriptPath = (
            FilePath(__file__).resolve().parents[2]
            / "re/automation/SolidworksReader.py"
        )

    # distinct destinations prevent similarly named native files from overwriting each others evidence
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
