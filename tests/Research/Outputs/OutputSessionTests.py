import hashlib as Hashing
import json as JsonCodec
import tempfile as TempFiles
from pathlib import Path as FilePath

from tests.Research.Outputs.SetOutputRunner import SetOutputRunner
from tests.Research.SupervisorClient import FixtureJob, InitStore, SessionHost


def CheckDurableOutputs() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Harness = SessionHost(RootPath, {"outputs": 1}, {"fixture.output": "outputs"})
        SetOutputRunner(Harness)
        Harness.SubmitJobs([FixtureJob("durable", "fixture.output", lease_seconds=30)])
        _ = Harness.RunIdle()
        assert Harness.ReadJob("durable")["state"] == "completed"
        Stored = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("durable")))
        Content = b"durable editable evidence candidate\x00\xff"
        Digest = Hashing.sha256(Content).hexdigest()
        assert Stored["output_artifacts_version"] == 1
        assert Stored["output_artifacts"] == {
            "native": {"sha256": Digest, "size_bytes": len(Content)}
        }
        assert Stored["result"]["artifacts"] == Stored["output_artifacts"]
        assert not any((RootPath / "SupervisorState/sessions").iterdir())
        assert not any((RootPath / "SupervisorState/claims").iterdir())
        assert Harness.StorePath is not None
        ObjectPath = Harness.StorePath / "objects" / Digest[:2] / Digest
        assert ObjectPath.read_bytes() == Content
        Harness.SubmitJobs(
            [FixtureJob("dependent", "fixture.output", depends_on=["durable"])]
        )
        _ = ObjectPath.write_bytes(b"corrupted output")
        _ = Harness.RunCli("jobs", "--job", "durable", ExitCode=1)
        _ = Harness.RunCli("run", "--idle-seconds", "1", ExitCode=1)


def CheckUnsafeOutputs() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        Harness = SessionHost(RootPath, {"outputs": 1}, {"fixture.output": "outputs"})
        SetOutputRunner(Harness)
        Modes = (
            "link",
            "ancestor",
            "hardlink",
            "traversal",
            "digest",
            "size",
            "duplicate",
            "rejected",
        )
        Harness.SubmitJobs(
            [
                FixtureJob(
                    Mode,
                    "fixture.output",
                    max_attempts=1,
                    lease_seconds=30,
                    options={"mode": Mode},
                )
                for Mode in Modes
            ]
        )
        _ = Harness.RunIdle()
        for Mode in Modes:
            Job = Harness.ReadJob(Mode)
            assert Job["state"] == "failed", Job
            Stored = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult(Mode)))
            assert Stored["result"] is None, Stored
            assert "output_artifacts" not in Stored
            assert str(Job["reason"]).startswith(
                ("invalid result:", "invalid output artifacts:")
            ), Job
        assert not any((RootPath / "SupervisorState/sessions").iterdir())


def CheckAdapterCapability() -> None:
    with TempFiles.TemporaryDirectory() as TempPath:
        RootPath = FilePath(TempPath).resolve()
        _ = InitStore(RootPath / "Store")
        LegacyFile = RootPath / "LegacyController.py"
        _ = LegacyFile.write_text(
            "from Adapters import A03Adapter\n\nclass LegacyController(A03Adapter):\n    OutputArtifactsVersion = 0\n",
            encoding="utf-8",
        )
        Harness = SessionHost(
            RootPath,
            {"outputs": 1},
            {"fixture.output": "outputs"},
            {
                "module": str(LegacyFile),
                "class": "LegacyController",
                "options": {"store": str(RootPath / "Store")},
            },
        )
        Harness.StorePath = RootPath / "Store"
        SetOutputRunner(Harness)
        Harness.SubmitJobs(
            [FixtureJob("unsupported", "fixture.output", max_attempts=1)]
        )
        _ = Harness.RunIdle()
        Job = Harness.ReadJob("unsupported")
        assert Job["state"] == "failed", Job
        assert "does not support version 1 output artifacts" in str(Job["reason"])
        Stored = JsonCodec.loads(JsonCodec.dumps(Harness.ReadResult("unsupported")))
        assert Stored["result"] is None
