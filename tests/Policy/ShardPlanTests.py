import json as JsonLib
import os as OsLib
import shutil as ShellUtil
import statistics as StatsLib
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


KReuseSuite = """
=== SampleHelper.py
def double(value):
    return value * 2
=== cases/one.txt
1
=== test_helper.py
import SampleHelper
def test_double():
    assert SampleHelper.double(2) == 4
=== test_data.py
from pathlib import Path
def test_data():
    assert (Path(__file__).parent / "cases" / "one.txt").read_text().strip() == "1"
=== test_listing.py
import os
def test_listing():
    assert "one.txt" in os.listdir(os.path.join(os.path.dirname(__file__), "cases"))
=== test_process.py
import subprocess, sys
def test_process():
    subprocess.run([sys.executable, "-c", "pass"], check=True)
=== test_plain.py
import pytest
def test_plain():
    assert True
def test_skipped():
    pytest.skip("skipped results are reusable")
"""

KGitConfig = [
    "-c",
    "user.name=ShardPlanTests",
    "-c",
    "user.email=shards@example.invalid",
]


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


def ReadWorkers(ReportPath: FilePath) -> set[str]:
    WorkerIds: set[str] = set()
    for LineText in ReportPath.read_text(encoding="utf-8").splitlines():
        Entry = JsonLib.loads(LineText)
        if Entry.get("$report_type") == "TestReport":
            WorkerIds.add(Entry["worker_id"])
    return WorkerIds


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
        ShardArgs = ["-m", "pytest", "-p", "no:cacheprovider", "--numprocesses", "2"]
        ShardArgs += ["--dist", "load", "--maxschedchunk", "1"]
        ShardArgs += [f"--report-log={ReportPath}", f"@{ArgsPath}"]
        ResultInfo = RunCommand(ShardArgs, SuitePath)
        assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
        assert ReadWorkers(ReportPath) == {"gw0", "gw1"}
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
        History = {TestIds[Index]: 0.1 + Index / 1e4 for Index in range(3, 600)}
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
        Median = StatsLib.median(History.values())
        for Shard in Shards:
            assert len(set(SlowIds) & set(Shard["TestIds"])) == 1
            assert Shard["TestIds"][0] in SlowIds
            Weights = [History.get(TestId, Median) for TestId in Shard["TestIds"]]
            assert Weights[0::2] == sorted(Weights[0::2], reverse=True)
            assert Weights[1::2] == sorted(Weights[1::2])
            assert Weights[1] == min(Weights)


def RunGit(ArgList: list[str], WorkPath: FilePath) -> bytes:
    GitArgs = ["git", *KGitConfig, "-c", "commit.gpgsign=false", *ArgList]
    ResultInfo = Subprocess.run(
        GitArgs, cwd=WorkPath, capture_output=True, check=False, timeout=60
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    return ResultInfo.stdout


def WriteSuite(SuitePath: FilePath, SuiteText: str) -> None:
    for Section in SuiteText.split("=== ")[1:]:
        NameText, _, BodyText = Section.partition("\n")
        TargetPath = SuitePath / NameText
        TargetPath.parent.mkdir(parents=True, exist_ok=True)
        _ = TargetPath.write_text(BodyText, encoding="utf-8")


def CommitSuite(SuitePath: FilePath, StepPath: FilePath) -> None:
    _ = RunGit(["add", "-A"], SuitePath)
    _ = RunGit(["commit", "-q", "--allow-empty", "-m", StepPath.name], SuitePath)
    StepPath.mkdir(parents=True)
    TreeBytes = RunGit(["ls-tree", "-r", "-z", "HEAD"], SuitePath)
    _ = (StepPath / "Tree.bin").write_bytes(TreeBytes)
    CollectArgs = ["-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"]
    Collected = RunCommand(CollectArgs, SuitePath)
    assert Collected.returncode == 0, Collected.stdout + Collected.stderr
    _ = (StepPath / "Collected.txt").write_text(Collected.stdout, encoding="utf-8")


def PlanStep(StepPath: FilePath, CachePath: FilePath | None) -> dict[str, object]:
    PlanPath = StepPath / "Plan" / "ShardPlan.json"
    PlanArgs = ["-m", "tools.TestShards.PlanShards", "--max-tests", "100"]
    PlanArgs += ["--collected", str(StepPath / "Collected.txt")]
    PlanArgs += ["--tree", str(StepPath / "Tree.bin"), "--output", str(PlanPath)]
    PlanArgs += ["--carried", str(StepPath / "Plan" / "Carried.json")]
    if CachePath is not None:
        PlanArgs += ["--cache", str(CachePath)]
    PlanInfo = RunCommand(PlanArgs, KRootPath)
    assert PlanInfo.returncode == 0, PlanInfo.stdout + PlanInfo.stderr
    PlanData: dict[str, object] = JsonLib.loads(PlanPath.read_text(encoding="utf-8"))
    return PlanData


def RunTracked(StepPath: FilePath, SuitePath: FilePath, TestIds: list[str]) -> None:
    ArgsPath = StepPath / "ShardTests.txt"
    _ = ArgsPath.write_text("\n".join(TestIds) + "\n", encoding="utf-8")
    ReportDir = StepPath / "Reports" / "1"
    ShardArgs = ["-m", "pytest", "-p", "no:cacheprovider"]
    ShardArgs += ["-p", "tools.TestShards.Reuse.Track.TrackHooks"]
    ShardArgs += [f"--test-deps={ReportDir}", "--numprocesses", "2"]
    ShardArgs += ["--dist", "load", "--maxschedchunk", "1"]
    ShardArgs += [f"--report-log={ReportDir / 'ShardReport.jsonl'}", f"@{ArgsPath}"]
    ResultInfo = Subprocess.run(
        [System.executable, *ShardArgs],
        cwd=SuitePath,
        env={**OsLib.environ, "PYTHONPATH": str(KRootPath)},
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stdout + ResultInfo.stderr
    assert sorted(OsLib.listdir(ReportDir)) == [
        "Deps-gw0.json",
        "Deps-gw1.json",
        "Deps-main.json",
        "ShardReport.jsonl",
    ]


def VerifyStep(StepPath: FilePath, CachePath: FilePath) -> str:
    PlanPath = str(StepPath / "Plan" / "ShardPlan.json")
    ReportsPath = str(StepPath / "Reports")
    MergeArgs = ["-m", "tools.TestShards.MergeReports", "--plan", PlanPath]
    MergeArgs += ["--reports", ReportsPath, "--output", str(StepPath / "Times.json")]
    Merged = RunCommand(MergeArgs, KRootPath)
    assert Merged.returncode == 0, Merged.stdout + Merged.stderr
    CacheArgs = ["-m", "tools.TestShards.Reuse.Cache.BuildCache", "--plan", PlanPath]
    CacheArgs += ["--carried", str(StepPath / "Plan" / "Carried.json")]
    CacheArgs += ["--reports", ReportsPath, "--tree", str(StepPath / "Tree.bin")]
    CacheArgs += ["--run", StepPath.name, "--output", str(CachePath)]
    Built = RunCommand(CacheArgs, KRootPath)
    assert Built.returncode == 0, Built.stdout + Built.stderr
    assert CachePath.is_file(), Built.stdout
    return Merged.stdout


def RunStep(
    SuitePath: FilePath, StepPath: FilePath, CachePath: FilePath | None
) -> tuple[dict[str, object], str]:
    CommitSuite(SuitePath, StepPath)
    PlanData = PlanStep(StepPath, CachePath)
    PlanText = (StepPath / "Plan" / "ShardPlan.json").read_text(encoding="utf-8")
    ShardList: list[dict[str, list[str]]] = JsonLib.loads(PlanText)["Shards"]
    assert len(ShardList) == 1
    RunTracked(StepPath, SuitePath, ShardList[0]["TestIds"])
    return PlanData, VerifyStep(StepPath, StepPath / "TestCache.json")


def ReadCache(CachePath: FilePath) -> dict[str, dict[str, dict[str, str]]]:
    CacheText = CachePath.read_text(encoding="utf-8")
    Modules: dict[str, dict[str, dict[str, str]]] = JsonLib.loads(CacheText)["Modules"]
    return Modules


def TestShardReuse() -> None:
    with Tempfile.TemporaryDirectory() as TempPath:
        WorkPath = FilePath(TempPath)
        SuitePath = StartSuite(WorkPath)
        FirstPlan, _ = RunStep(SuitePath, WorkPath / "First", None)
        assert FirstPlan["Reused"] == {"Run": "", "Outcomes": {}, "Seconds": {}}
        Recorded = ReadCache(WorkPath / "First" / "TestCache.json")
        assert sorted(Recorded) == [
            "test_data.py",
            "test_helper.py",
            "test_listing.py",
            "test_plain.py",
        ]
        assert "SampleHelper.py" in Recorded["test_helper.py"]["Files"]
        assert "cases/one.txt" in Recorded["test_data.py"]["Files"]
        assert "cases" in Recorded["test_listing.py"]["Folders"]
        ChangeSuite(SuitePath)
        ConfirmReuse(WorkPath)


def StartSuite(WorkPath: FilePath) -> FilePath:
    SuitePath = WorkPath / "Suite"
    SuitePath.mkdir()
    _ = RunGit(["init", "-q"], SuitePath)
    _ = (SuitePath / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
    _ = (SuitePath / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    WriteSuite(SuitePath, KReuseSuite)
    return SuitePath


def ChangeSuite(SuitePath: FilePath) -> None:
    HelperText = "def double(value):\n    return value + value\n"
    _ = (SuitePath / "SampleHelper.py").write_text(HelperText, encoding="utf-8")
    _ = (SuitePath / "cases" / "two.txt").write_text("2\n", encoding="utf-8")


def ConfirmReuse(WorkPath: FilePath) -> None:
    SuitePath = WorkPath / "Suite"
    FirstCache = WorkPath / "First" / "TestCache.json"
    SecondPlan, SecondText = RunStep(SuitePath, WorkPath / "Second", FirstCache)
    assert SecondPlan["Reused"] == {
        "Run": "First",
        "Outcomes": {
            "test_data.py::test_data": "passed",
            "test_plain.py::test_plain": "passed",
            "test_plain.py::test_skipped": "skipped",
        },
        "Seconds": {},
    }
    assert "3 tests reused results that merge-group run First verified" in SecondText
    assert sorted(ReadCache(WorkPath / "Second" / "TestCache.json")) == sorted(
        ReadCache(FirstCache)
    )
    SecondCache = WorkPath / "Second" / "TestCache.json"
    ThirdPlan, ThirdText = RunStep(SuitePath, WorkPath / "Third", SecondCache)
    assert ThirdPlan["Shards"] == [
        {"Index": 1, "Estimate": 1.0, "TestIds": ["test_process.py::test_process"]}
    ]
    assert "5 tests reused results that merge-group run Second verified" in ThirdText
