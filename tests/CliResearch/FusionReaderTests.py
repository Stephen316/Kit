from json import loads as LoadJson
from pathlib import Path as FilePath

from tests.CliResearch.CheckReceipt import CheckReceipt
from tests.CliResearch.DirectReader import DirectReader
from tests.CliResearch.ResearchAssets import KArchiveAsset, KControlAsset
from tests.CliResearch.ResearchClient import ResearchCli


# fusion dispatch must preserve direct reader artifacts and partial archive exit semantics
def CheckFusReceipt(TmpPath: FilePath) -> None:
    Direct = TmpPath / "Direct"
    Bridged = TmpPath / "Bridged"
    Arguments = ("--asset", KControlAsset, "--asset", KArchiveAsset, "--allow-partial")
    Reference = DirectReader(
        TmpPath, "FusionReader.py", *Arguments, "--output", str(Direct)
    )
    Result = ResearchCli(TmpPath, "fusion", *Arguments, "--output", str(Bridged))
    assert Reference.returncode == Result.returncode, (Reference.stderr, Result.stderr)
    assert Result.returncode in (0, 3)
    DirectFiles = {
        Value.relative_to(Direct): Value.read_bytes()
        for Value in Direct.rglob("*")
        if Value.is_file()
    }
    assert DirectFiles == {
        Value.relative_to(Bridged): Value.read_bytes()
        for Value in Bridged.rglob("*")
        if Value.is_file()
    }
    Receipts = list(Bridged.rglob("receipt.json"))
    assert Receipts
    for ReceiptPath in Receipts:
        CheckReceipt(ReceiptPath.parent)
    Summary = LoadJson((Bridged / "summary.json").read_bytes())
    assert Summary["counts"]["assets"] == 2 and Summary["counts"]["decoded"] >= 1
    assert Summary["allow_partial"] is True and Summary["portable_complete"] is False
    Rejected = ResearchCli(
        TmpPath,
        "fusion",
        "--asset",
        KArchiveAsset,
        "--output",
        str(TmpPath / "Rejected"),
    )
    assert Rejected.returncode == 3, Rejected.stderr
    assert (TmpPath / "Rejected/summary.json").is_file()
