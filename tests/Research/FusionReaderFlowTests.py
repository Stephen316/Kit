import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.FusionChecks import VerifyControl
from tests.Research.FusionClient import KArchiveAsset, KControlAsset, RunFusionReader


def CheckFusionFlow() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        TargetPath = FilePath(TempPath) / "Decoded"
        ArgumentList = ["--asset", KControlAsset, "--output", str(TargetPath)]
        ResultInfo = RunFusionReader(ArgumentList)
        assert ResultInfo.returncode == 0, ResultInfo.stderr
        Summary = JsonCodec.loads((TargetPath / "summary.json").read_text())
        assert JsonCodec.loads(ResultInfo.stdout)["counts"] == Summary["counts"]
        assert Summary["counts"]["strict"] == 1
        assert Summary["counts"]["partial"] == 0
        assert Summary["allow_partial"] is False
        assert Summary["portable_complete"] is False
        Entry = Summary["assets"][0]
        assert Entry["path"] == KControlAsset
        assert Entry["outcome"] == "decoded"
        assert Entry["reader_mode"] == "strict"
        VerifyControl(TargetPath, Entry)
        PriorData = (TargetPath / "summary.json").read_bytes()
        ResultInfo = RunFusionReader(ArgumentList)
        assert ResultInfo.returncode == 1
        assert (TargetPath / "summary.json").read_bytes() == PriorData


def CheckArchive() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        TargetPath = FilePath(TempPath) / "Rejected"
        ResultInfo = RunFusionReader(
            ["--asset", KArchiveAsset, "--output", str(TargetPath)]
        )
        assert ResultInfo.returncode == 3, ResultInfo.stderr
        Summary = JsonCodec.loads((TargetPath / "summary.json").read_text())
        Entry = Summary["assets"][0]
        assert Entry["path"] == KArchiveAsset
        assert Entry["outcome"] in ("rejected", "reader_error")
        assert Entry["reason"]
        assert "directory" not in Entry
        assert Summary["counts"]["decoded"] == 0
        assert [EntryPath.name for EntryPath in TargetPath.iterdir()] == [
            "summary.json"
        ]
