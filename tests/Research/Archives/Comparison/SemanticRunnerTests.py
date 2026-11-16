from dataclasses import replace as ChangeRecord
from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as MarkValue

from interchange.serialization.JsonCodec import DumpJson
from tests.Research.Archives.Comparison.SemanticComparisonTests import KTolerances
from tests.Research.Archives.Comparison.SemanticDocuments import (
    ChangeSemantic,
    MakeDocument,
    MakeSymmetric,
)
from tests.Research.SupervisorClient import FixtureJob, SessionHost

# subprocess integration must use the same checkout as the authored comparison fixtures
KRepoRoot = FilePath(__file__).resolve().parents[4]


# real schema generation and controller binding keep worker execution inside production process contracts
def PrepareWorker(TmpPath: FilePath) -> SessionHost:
    Harness = SessionHost(TmpPath, {"semantics": 1}, {"semantic.compare": "semantics"})
    WorkerPath = KRepoRoot / "re/automation/SemanticComparisonRunner.py"
    Process = RunProcess(
        [PythonExe, str(WorkerPath), "--schema"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert Process.returncode == 0, Process.stderr
    SchemaPath = TmpPath / "SemanticSchema.json"
    _ = SchemaPath.write_text(Process.stdout, encoding="utf-8")
    RegistryPath = FilePath(
        ParseJson(Harness.ConfigFile.read_text(encoding="utf-8"))["registry"]
    )
    Registry = ParseJson(RegistryPath.read_text(encoding="utf-8"))
    Entry = Registry["runners"]["semantic.compare"]
    Entry["argv"] = [PythonExe, str(WorkerPath), "{session}"]
    Entry["result_schema"] = str(SchemaPath)
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")
    return Harness


# job seals must come from content binding rather than invented worker packet shortcuts
def SubmitCompare(
    Harness: SessionHost, FirstBytes: bytes, SecondBytes: bytes, Missing: bool = False
) -> None:
    Harness.BindBytes("first-document", FirstBytes)
    Harness.BindBytes("second-document", SecondBytes)
    Harness.BindBytes("comparison-tolerances", EncodeJson(KTolerances).encode())
    Inputs = {
        "first": "first-document",
        "second": "second-document",
        "tolerances": "comparison-tolerances",
    }
    if Missing:
        del Inputs["tolerances"]
    Harness.SubmitJobs(
        [
            FixtureJob(
                "comparison",
                "semantic.compare",
                inputs=Inputs,
                options={
                    "scope": "authored-comparison",
                    "first_geometry_unit": "mm",
                    "second_geometry_unit": "mm",
                    "max_candidates": 20000,
                },
                max_attempts=1,
                lease_seconds=30,
            )
        ]
    )
    _ = Harness.RunIdle()


# artifacts larger than metadata limits must survive intake and session cleanup without qualifying native output
def CheckDurable(TmpPath: FilePath) -> None:
    Harness = PrepareWorker(TmpPath)
    Document = MakeDocument()
    Changes = {
        NameText: tuple(
            ChangeRecord(Record, name="a" * 65536)
            for Record in getattr(Document, NameText)
        )
        for NameText in (
            "parameters",
            "support_planes",
            "sketches",
            "feature_timeline",
            "bodies",
            "configurations",
        )
    }
    Content = DumpJson(ChangeRecord(Document, **Changes)).encode()
    SubmitCompare(Harness, Content, Content)
    JobInfo = Harness.ReadJob("comparison")
    assert JobInfo["state"] == "completed", JobInfo
    Stored = ParseJson(EncodeJson(Harness.ReadResult("comparison")))
    Records = Stored["result"]["records"]
    assert len(EncodeJson(Stored).encode()) < 1024 * 1024
    assert Records["semantic_qualification"] == "unverified"
    assert Records["native_acceptance"] == "not_established"
    assert Records["status"] == "equal_observed_graph"
    Artifact = Stored["output_artifacts"]["semantic-report"]
    assert 1024 * 1024 < Artifact["size_bytes"] <= 32 * 1024 * 1024
    assert Harness.StorePath is not None
    ObjectPath = (
        Harness.StorePath / "objects" / Artifact["sha256"][:2] / Artifact["sha256"]
    )
    ReportBytes = ObjectPath.read_bytes()
    assert (
        DigestBytes(ReportBytes).hexdigest()
        == Records["report_sha256"]
        == Artifact["sha256"]
    )
    assert len(ReportBytes) == Records["report_size_bytes"] == Artifact["size_bytes"]
    Report = ParseJson(ReportBytes)
    assert (
        Records["input_sha256"]
        == Report["input_sha256"]
        == {
            "left": DigestBytes(Content).hexdigest(),
            "right": DigestBytes(Content).hexdigest(),
            "tolerances": DigestBytes(EncodeJson(KTolerances).encode()).hexdigest(),
        }
    )
    assert (
        Report["execution"]["fingerprint"]
        == Records["fingerprint"]
        == JobInfo["fingerprint"]
    )
    assert Report["execution"]["definition_sha256"] == Records["definition_sha256"]
    assert not any((TmpPath / "SupervisorState/sessions").iterdir())


# a completed observation can report differences and ambiguity while preserving unverified qualification
@MarkValue.parametrize("StatusName", ("different", "ambiguous"))
def CheckObserved(TmpPath: FilePath, StatusName: str) -> None:
    Harness = PrepareWorker(TmpPath)
    First = MakeSymmetric() if StatusName == "ambiguous" else MakeDocument()
    Second = First if StatusName == "ambiguous" else ChangeSemantic(First, "dependency")
    SubmitCompare(Harness, DumpJson(First).encode(), DumpJson(Second).encode())
    assert Harness.ReadJob("comparison")["state"] == "completed"
    Stored = ParseJson(EncodeJson(Harness.ReadResult("comparison")))
    assert Stored["result"]["records"]["status"] == StatusName
    assert Stored["result"]["records"]["semantic_qualification"] == "unverified"
    assert Stored["output_artifacts_version"] == 1


# missing seals must fail the actual worker process before any semantic artifact becomes durable
def CheckMissingPin(TmpPath: FilePath) -> None:
    Harness = PrepareWorker(TmpPath)
    Content = DumpJson(MakeDocument()).encode()
    SubmitCompare(Harness, Content, Content, Missing=True)
    assert Harness.ReadJob("comparison")["state"] == "failed"
    Stored = ParseJson(EncodeJson(Harness.ReadResult("comparison")))
    assert Stored["result"] is None
    assert "output_artifacts" not in Stored
