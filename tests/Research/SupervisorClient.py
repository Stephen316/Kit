import json as JsonCodec
import os as OsLayer
import subprocess as Subprocess
import sys as System
import time as TimeClock
from pathlib import Path as FilePath

KRepoRoot = FilePath(__file__).resolve().parents[2]
KResultSchema = {
    "type": "object",
    "required": ["count", "inputs", "tokenless"],
    "additionalProperties": False,
    "properties": {
        "count": {"type": "integer", "minimum": 0},
        "inputs": {"type": "array", "items": {"type": "string"}},
        "tokenless": {"type": "boolean", "const": True},
    },
}


def WriteRegistry(RootPath: FilePath, KindPools: dict[str, str]) -> FilePath:
    SchemaFile = RootPath / "ResultSchema.json"
    _ = SchemaFile.write_text(JsonCodec.dumps(KResultSchema), encoding="utf-8")
    RunnerArgs = [
        System.executable,
        str(KRepoRoot / "tests/Research/SessionRunner.py"),
        "{session}",
    ]
    Registry = {
        "runners": {
            KindName: {
                "pool": PoolName,
                "argv": RunnerArgs,
                "result_schema": str(SchemaFile),
            }
            for KindName, PoolName in KindPools.items()
        }
    }
    RegistryFile = RootPath / "Runners.json"
    _ = RegistryFile.write_text(JsonCodec.dumps(Registry), encoding="utf-8")
    return RegistryFile


def InitStore(StorePath: FilePath) -> dict[str, object]:
    ResultInfo = Subprocess.run(
        [
            System.executable,
            str(KRepoRoot / "re/automation/Controller.py"),
            "--store",
            str(StorePath),
            "init",
            "--max-running",
            "8",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert ResultInfo.returncode == 0, ResultInfo.stderr
    return {"adapter": "a03", "store": str(StorePath)}


def WriteConfig(
    RootPath: FilePath,
    RegistryFile: FilePath,
    PoolLimits: dict[str, int],
    Controller: dict[str, object],
) -> FilePath:
    ConfigFile = RootPath / "Supervisor.json"
    ConfigInfo = {
        "state": str(RootPath / "SupervisorState"),
        "controller": Controller,
        "registry": str(RegistryFile),
        "worker": "supervisor:fixture",
        "pools": {
            PoolName: {"max_sessions": Limit}
            for PoolName, Limit in PoolLimits.items()
        },
        "stop_grace_seconds": 1,
        "poll_seconds": 0.1,
    }
    _ = ConfigFile.write_text(JsonCodec.dumps(ConfigInfo), encoding="utf-8")
    return ConfigFile


class SessionCommand:
    def __init__(self, ConfigFile: FilePath) -> None:
        super().__init__()
        self.ConfigFile = ConfigFile
        self.Command = [
            System.executable,
            str(KRepoRoot / "re/automation/Supervisor.py"),
            "--config",
            str(ConfigFile),
        ]

    def RunCli(self, *ArgItems: str, ExitCode: int = 0, Timeout: int = 60) -> str:
        ResultInfo = Subprocess.run(
            self.Command + list(ArgItems),
            capture_output=True,
            text=True,
            check=False,
            timeout=Timeout,
        )
        assert ResultInfo.returncode == ExitCode, ResultInfo.stderr
        return ResultInfo.stdout

    def StartRun(self, *ArgItems: str) -> "Subprocess.Popen[str]":
        return Subprocess.Popen(
            self.Command + ["run", *ArgItems],
            stdout=Subprocess.PIPE,
            stderr=Subprocess.PIPE,
            text=True,
        )

    def RunIdle(self, IdleSeconds: float = 3, MaxSeconds: float = 60) -> list[object]:
        Output = self.RunCli(
            "run",
            "--idle-seconds",
            str(IdleSeconds),
            "--max-seconds",
            str(MaxSeconds),
            Timeout=int(MaxSeconds) + 60,
        )
        return [JsonCodec.loads(LineText) for LineText in Output.splitlines()]


class SessionRecords(SessionCommand):
    def __init__(
        self, RootPath: FilePath, StorePath: FilePath | None, ConfigFile: FilePath
    ) -> None:
        super().__init__(ConfigFile)
        self.RootPath = RootPath
        self.StorePath = StorePath

    def SubmitJobs(self, JobList: list[dict[str, object]]) -> None:
        BatchFile = self.RootPath / "Batch.json"
        _ = BatchFile.write_text(JsonCodec.dumps({"jobs": JobList}), encoding="utf-8")
        _ = self.RunCli("submit", str(BatchFile))

    def BindBytes(self, BindName: str, Content: bytes) -> None:
        InputFile = self.RootPath / "Input.bin"
        _ = InputFile.write_bytes(Content)
        _ = self.RunCli("bind", BindName, str(InputFile))

    def ReadJob(self, JobName: str) -> dict[str, object]:
        JobInfo: dict[str, object] = JsonCodec.loads(
            self.RunCli("jobs", "--job", JobName)
        )["jobs"][0]
        return JobInfo

    def ReadResult(self, JobName: str) -> dict[str, object]:
        ResultHash = str(self.ReadJob(JobName)["result"])
        if self.StorePath is not None:
            ResultPath = self.StorePath / "objects" / ResultHash[:2] / ResultHash
        else:
            ResultPath = self.RootPath / "Mini" / "objects" / ResultHash
        ResultInfo: dict[str, object] = JsonCodec.loads(
            ResultPath.read_text(encoding="utf-8")
        )
        return ResultInfo


class SessionHost(SessionRecords):
    def __init__(
        self,
        RootPath: FilePath,
        PoolLimits: dict[str, int],
        KindPools: dict[str, str],
        Controller: dict[str, object] | None = None,
    ) -> None:
        RegistryFile = WriteRegistry(RootPath, KindPools)
        StorePath = None
        if Controller is None:
            StorePath = RootPath / "Store"
            Controller = InitStore(StorePath)
        ConfigFile = WriteConfig(RootPath, RegistryFile, PoolLimits, Controller)
        super().__init__(RootPath, StorePath, ConfigFile)

    def WaitReason(self, JobName: str, Reason: str, Timeout: float = 30) -> None:
        Until = TimeClock.monotonic() + Timeout
        while TimeClock.monotonic() < Until:
            if self.ReadJob(JobName)["reason"] == Reason:
                return
            TimeClock.sleep(0.1)
        raise AssertionError(f"{JobName} never reported {Reason}")

    def WaitSession(
        self, JobName: str | None = None, Timeout: float = 30
    ) -> dict[str, object]:
        SessionRoot = self.RootPath / "SupervisorState" / "sessions"
        Until = TimeClock.monotonic() + Timeout
        while TimeClock.monotonic() < Until:
            for RecordFile in sorted(SessionRoot.glob("*/session.json")):
                try:
                    SessionInfo: dict[str, object] = JsonCodec.loads(
                        RecordFile.read_text(encoding="utf-8")
                    )
                except (OSError, ValueError):
                    continue
                if JobName is None or SessionInfo.get("job_id") == JobName:
                    return SessionInfo
            TimeClock.sleep(0.1)
        raise AssertionError("no supervised session started")


def IsProcessGone(ProcessId: int) -> bool:
    try:
        OsLayer.kill(ProcessId, 0)
    except ProcessLookupError:
        return True
    StatFile = FilePath(f"/proc/{ProcessId}/stat")
    try:
        StatText = StatFile.read_text(encoding="ascii")
    except FileNotFoundError:
        return FilePath("/proc/self/stat").is_file()
    return StatText[StatText.rindex(")") + 2] == "Z"


def IsGoneByTimeout(ProcessId: int, Timeout: float = 15) -> bool:
    Until = TimeClock.monotonic() + Timeout
    while TimeClock.monotonic() < Until:
        if IsProcessGone(ProcessId):
            return True
        TimeClock.sleep(0.1)
    return IsProcessGone(ProcessId)


def FixtureJob(JobName: str, KindName: str, **Settings: object) -> dict[str, object]:
    JobInfo: dict[str, object] = {
        "id": JobName,
        "kind": KindName,
        "inputs": {},
        "rule_version": "rule@1",
        "tool_version": "tool@1",
        "max_attempts": 2,
        "lease_seconds": 3,
        "timeout_seconds": 60,
        "retry_base_seconds": 1,
    }
    JobInfo.update(Settings)
    return JobInfo
