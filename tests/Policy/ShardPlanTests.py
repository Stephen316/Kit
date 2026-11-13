import json as JsonLib
import shutil as ShellUtil
import subprocess as Subprocess
import sys as System
import tempfile as Tempfile
from pathlib import Path as FilePath

KRootPath = FilePath(__file__).resolve().parents[2]

KSampleSuite = """
import pytest


@pytest.mark.parametrize("value", range(5))
def test_value(value):
    assert value >= 0


def test_skip():
    pytest.skip("covered by the shard report")


class TestGroup:
    def test_one(self):
        assert True

    def test_two(self):
        assert True
"""


def RunCommand(
    ArgList: list[str], WorkPath: FilePath
) -> Subprocess.CompletedProcess[str]:
    return Subprocess.run(
        [System.executable, *ArgList],
        cwd=WorkPath,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )


def PlanSample(SuitePath: FilePath) -> tuple[FilePath, list[str]]:
    _ = (SuitePath / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    _ = (SuitePath / "test_sample.py").write_text(KSampleSuite, encoding="utf-8")
    CollectArgs = ["-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
    Collected = RunCommand(CollectArgs, SuitePath)
    assert Collected.returncode == 0, Collected.stdout + Collected.stderr
    _ = (SuitePath / "Collected.txt").write_text(Collected.stdout, encoding="utf-8")
    PlanPath = SuitePath / "Plan" / "ShardPlan.json"
    PlanArgs = ["-m", "tools.TestShards.PlanShards", "--max-tests", "3"]
    PlanArgs += ["--collected", str(SuitePath / "Collected.txt")]
    PlanArgs += ["--history", str(SuitePath / "Missing.json")]
    PlanInfo = RunCommand([*PlanArgs, "--output", str(PlanPath)], KRootPath)
    assert PlanInfo.returncode == 0, PlanInfo.stderr
    return PlanPath, Collected.stdout.split("\n\n")[0].split("\n")


def RunShards(PlanPath: FilePath, SuitePath: FilePath) -> list[str]:
    PlanData = JsonLib.loads(PlanPath.read_text(encoding="utf-8"))
    ShardIds: list[str] = []
    for ShardData in PlanData["Shards"]:
        IndexText = str(ShardData["Index"])
        ArgsPath = SuitePath / f"Shard{IndexText}.txt"
        _ = ArgsPath.write_text(
            "\n".join(ShardData["TestIds"]) + "\n", encoding="utf-8"
        )
        ReportPath = SuitePath / "Reports" / IndexText / "ShardReport.jsonl"
        ShardArgs = ["-m", "pytest", "-p", "no:cacheprovider"]
        ShardArgs += [f"--report-log={ReportPath}", f"@{ArgsPath}"]
        ResultInfo = RunCommand(ShardArgs, SuitePath)
        assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
        ShardIds.extend(ShardData["TestIds"])
    return ShardIds


def VerifyLoss(MergeArgs: list[str], SuitePath: FilePath) -> None:
    ShellUtil.rmtree(SuitePath / "Reports" / "2")
    Missing = RunCommand(MergeArgs, KRootPath)
    assert Missing.returncode == 1
    assert "expected 3 shard report logs but found 2" in Missing.stdout
    ErrorLines = [
        LineText
        for LineText in Missing.stdout.splitlines()
        if LineText.startswith("::error::")
    ]
    assert sum(LineText.endswith(" never ran") for LineText in ErrorLines) == 3


def TestShardFlow() -> None:
    with Tempfile.TemporaryDirectory() as TempPath:
        SuitePath = FilePath(TempPath)
        PlanPath, CollectedIds = PlanSample(SuitePath)
        PlanData = JsonLib.loads(PlanPath.read_text(encoding="utf-8"))
        assert [len(Shard["TestIds"]) for Shard in PlanData["Shards"]] == [3, 3, 2]
        ShardIds = RunShards(PlanPath, SuitePath)
        assert sorted(ShardIds) == sorted(CollectedIds)
        MergeArgs = ["-m", "tools.TestShards.MergeReports", "--plan", str(PlanPath)]
        MergeArgs += ["--reports", str(SuitePath / "Reports")]
        MergeArgs += ["--output", str(SuitePath / "Durations.json")]
        Merged = RunCommand(MergeArgs, KRootPath)
        assert Merged.returncode == 0, Merged.stdout + Merged.stderr
        assert "7 passed" in Merged.stdout and "1 skipped" in Merged.stdout
        Recorded = JsonLib.loads((SuitePath / "Durations.json").read_text())
        assert sorted(Recorded["Durations"]) == sorted(ShardIds)
        VerifyLoss(MergeArgs, SuitePath)


def TestShardCap() -> None:
    with Tempfile.TemporaryDirectory() as TempPath:
        WorkPath = FilePath(TempPath)
        TestIds = [f"tests/SampleTests.py::TestCase{Index}" for Index in range(650)]
        CollectedText = "\n".join(TestIds) + "\n\n650 tests collected in 0.10s\n"
        _ = (WorkPath / "Collected.txt").write_text(CollectedText, encoding="utf-8")
        SlowIds = TestIds[:3]
        History = {TestId: 0.1 for TestId in TestIds[3:600]}
        History.update({TestId: 90.0 for TestId in SlowIds})
        HistoryText = JsonLib.dumps({"Durations": History})
        _ = (WorkPath / "History.json").write_text(HistoryText, encoding="utf-8")
        PlanPath = WorkPath / "ShardPlan.json"
        PlanArgs = ["-m", "tools.TestShards.PlanShards", "--max-tests", "300"]
        PlanArgs += ["--collected", str(WorkPath / "Collected.txt")]
        PlanArgs += ["--history", str(WorkPath / "History.json")]
        PlanInfo = RunCommand([*PlanArgs, "--output", str(PlanPath)], KRootPath)
        assert PlanInfo.returncode == 0, PlanInfo.stderr
        assert "650 tests across 3 shards" in PlanInfo.stdout
        Shards = JsonLib.loads(PlanPath.read_text(encoding="utf-8"))["Shards"]
        assert all(len(Shard["TestIds"]) <= 300 for Shard in Shards)
        Assigned = [TestId for Shard in Shards for TestId in Shard["TestIds"]]
        assert sorted(Assigned) == sorted(TestIds)
        for Shard in Shards:
            assert len(set(SlowIds) & set(Shard["TestIds"])) == 1
            Positions = [TestIds.index(TestId) for TestId in Shard["TestIds"]]
            assert Positions == sorted(Positions)
