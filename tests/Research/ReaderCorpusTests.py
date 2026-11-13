import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath


def CheckReadCorpus() -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Manifest = JsonCodec.loads((RootPath / "re/automation/Corpus.json").read_text())
    AssetList = [
        Asset for Asset in Manifest["assets"] if Asset.get("format") == "sldprt"
    ]
    assert len(AssetList) == 58
    Counts = {"decoded": 0, "rejected": 0}
    with TempFiles.TemporaryDirectory() as TempPath:
        for Index, Asset in enumerate(AssetList):
            OutputPath = FilePath(TempPath) / str(Index)
            ResultInfo = Subprocess.run(
                [
                    System.executable,
                    str(RootPath / "re/automation/SolidworksReader.py"),
                    "--asset",
                    Asset["path"],
                    "--output",
                    str(OutputPath),
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            assert ResultInfo.returncode in (0, 1), ResultInfo.stderr
            if ResultInfo.returncode:
                assert not OutputPath.exists()
                assert JsonCodec.loads(ResultInfo.stderr)["error"]
                Counts["rejected"] += 1
                continue
            Receipt = JsonCodec.loads((OutputPath / "receipt.json").read_text())
            assert Receipt["source"] == Asset
            assert Receipt["semantic_qualification"] == "unverified"
            assert Receipt["unresolved"]
            assert Receipt["portable_complete"] is False
            Counts["decoded"] += 1
        assert Counts["decoded"] > 0
        print(JsonCodec.dumps({"reader_corpus": Counts}, sort_keys=True))
