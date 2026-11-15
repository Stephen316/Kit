from pathlib import Path as FilePath

from tests.CliResearch.CheckReceipt import CheckReceipt
from tests.CliResearch.DirectReader import DirectReader
from tests.CliResearch.ResearchAssets import KSwAsset
from tests.CliResearch.ResearchClient import ResearchCli


# solidworks dispatch must preserve reader receipts and refuse overwriting existing artifacts
def CheckSwReceipts(TmpPath: FilePath) -> None:
    Direct = TmpPath / "Direct"
    Bridged = TmpPath / "Bridged"
    Arguments = ("--asset", KSwAsset)
    Reference = DirectReader(
        TmpPath, "SolidworksReader.py", *Arguments, "--output", str(Direct)
    )
    Result = ResearchCli(TmpPath, "solidworks", *Arguments, "--output", str(Bridged))
    assert Reference.returncode == Result.returncode == 0, (
        Reference.stderr,
        Result.stderr,
    )
    assert {Value.name for Value in Direct.iterdir()} == {
        "document.json",
        "receipt.json",
    }
    assert {Value.name for Value in Bridged.iterdir()} == {
        "document.json",
        "receipt.json",
    }
    for FileName in ("document.json", "receipt.json"):
        assert (Direct / FileName).read_bytes() == (Bridged / FileName).read_bytes()
    CheckReceipt(Bridged)
    Before = {Value.name: Value.read_bytes() for Value in Bridged.iterdir()}
    Repeated = ResearchCli(TmpPath, "solidworks", *Arguments, "--output", str(Bridged))
    assert Repeated.returncode == 1
    assert {Value.name: Value.read_bytes() for Value in Bridged.iterdir()} == Before
