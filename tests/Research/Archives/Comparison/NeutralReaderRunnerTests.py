from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import run as RunProcess
from sys import executable as PythonExe

from pytest import mark as MarkValue

from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Container.Format import KitDocStream
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.JsonCodec import LoadJson
from tests.Research.Archives.Comparison.SemanticComparisonTests import KTolerances
from tests.Research.SupervisorClient import FixtureJob, SessionHost

# tracked current checkout captures keep process coverage independent of unavailable historical commits
KRepoRoot = FilePath(__file__).resolve().parents[4]

# each raw source control remains independently captured rather than a kit neutral carrier
KControls = {
    "fusion.f3d": "P01/fusion-5dc3245eb59c/P01-fusion-baseline-a.f3d",
    "solidworks.sldprt": "P01/solidworks-75b9308cf13e/P01-solidworks-baseline-a.SLDPRT",
}


# both registered processes must execute their actual schemas and artifact intake contracts
def PrepareReaders(TmpPath: FilePath) -> SessionHost:
    Harness = SessionHost(
        TmpPath,
        {"research": 1},
        {"reader.neutral": "research", "semantic.compare": "research"},
    )
    RegistryPath = FilePath(
        ParseJson(Harness.ConfigFile.read_text(encoding="utf-8"))["registry"]
    )
    Registry = ParseJson(RegistryPath.read_text(encoding="utf-8"))
    for KindName, WorkerName in (
        ("reader.neutral", "NeutralReaderRunner.py"),
        ("semantic.compare", "SemanticComparisonRunner.py"),
    ):
        WorkerPath = KRepoRoot / "re/automation" / WorkerName
        Process = RunProcess(
            [PythonExe, str(WorkerPath), "--schema"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert Process.returncode == 0, Process.stderr
        SchemaPath = TmpPath / f"{KindName}.json"
        _ = SchemaPath.write_text(Process.stdout, encoding="utf-8")
        Registry["runners"][KindName]["argv"] = [
            PythonExe,
            str(WorkerPath),
            "{session}",
        ]
        Registry["runners"][KindName]["result_schema"] = str(SchemaPath)
    _ = RegistryPath.write_text(EncodeJson(Registry), encoding="utf-8")
    return Harness


# native options remain fixed before scheduling rather than changing strictness after a refusal
def ReaderOptions(FormatName: str) -> dict[str, object]:
    return {
        "scope": "current-p01-observation",
        "source_format": FormatName,
        "strict": False,
        "configuration": None,
    }


# immutable object retrieval verifies artifact seals independently from compact controller receipts
def ReadArtifact(Harness: SessionHost, Artifact: dict[str, object]) -> bytes:
    assert Harness.StorePath is not None
    Digest = str(Artifact["sha256"])
    Content = (Harness.StorePath / "objects" / Digest[:2] / Digest).read_bytes()
    assert DigestBytes(Content).hexdigest() == Digest
    assert len(Content) == Artifact["size_bytes"]
    return Content


# actual native inputs must survive durable selector chaining without turning retained evidence into qualification
@MarkValue.parametrize("FormatName", tuple(KControls))
def CheckNativeFlow(TmpPath: FilePath, FormatName: str) -> None:
    Harness = PrepareReaders(TmpPath)
    SourcePath = KRepoRoot / "re/automation/PairedCaptures" / KControls[FormatName]
    SourceBytes = SourcePath.read_bytes()
    Harness.BindBytes("native-control", SourceBytes)
    Harness.BindBytes("five-tolerances", EncodeJson(KTolerances).encode())
    Selector = {"dependency": "read-native", "artifact": "neutral-document"}
    Harness.SubmitJobs(
        [
            FixtureJob(
                "read-native",
                "reader.neutral",
                inputs={"source": "native-control"},
                options=ReaderOptions(FormatName),
                max_attempts=1,
                lease_seconds=30,
            ),
            FixtureJob(
                "compare-native",
                "semantic.compare",
                depends_on=["read-native"],
                inputs={
                    "first": Selector,
                    "second": Selector,
                    "tolerances": "five-tolerances",
                },
                options={
                    "scope": "native-self-observation",
                    "first_geometry_unit": "mm",
                    "second_geometry_unit": "mm",
                    "max_candidates": 20000,
                },
                max_attempts=1,
                lease_seconds=30,
            ),
        ]
    )
    _ = Harness.RunIdle(MaxSeconds=120)
    assert Harness.ReadJob("read-native")["state"] == "completed"
    assert Harness.ReadJob("compare-native")["state"] == "completed"
    Stored = ParseJson(EncodeJson(Harness.ReadResult("read-native")))
    Records = Stored["result"]["records"]
    assert Records["source_sha256"] == DigestBytes(SourceBytes).hexdigest()
    assert Records["fingerprint"] == Harness.ReadJob("read-native")["fingerprint"]
    assert Records["implementation"]["sdk_source_files"] > 0
    assert (
        Records["implementation"]["tool_sources_sha256"]["NeutralReaderRunner.py"]
        == DigestBytes(
            (KRepoRoot / "re/automation/NeutralReaderRunner.py").read_bytes()
        ).hexdigest()
    )
    assert Records["read_options"] == {
        "strict": False,
        "configuration": None,
        "include_brep": True,
        "include_tessellation": True,
    }
    assert Records["portable_complete"] is False
    assert Records["semantic_qualification"] == "unverified"
    assert Records["native_acceptance"] == "not_established"
    Neutral = ReadArtifact(Harness, Stored["output_artifacts"]["neutral-document"])
    Document = LoadJson(Neutral.decode())
    assert isinstance(Document, CadDocument)
    Document.assert_valid()
    assert Document.source.sha256 == Records["source_sha256"]
    assert Document.metadata or Document.brep_payloads or Document.diagnostics
    Evidence = ParseJson(
        ReadArtifact(Harness, Stored["output_artifacts"]["reader-evidence"])
    )
    assert (
        Evidence["neutral_sha256"]
        == Records["neutral_sha256"]
        == DigestBytes(Neutral).hexdigest()
    )
    assert Evidence["unresolved"] and Evidence["portable_complete"] is False
    Compared = ParseJson(EncodeJson(Harness.ReadResult("compare-native")))
    Report = ParseJson(
        ReadArtifact(Harness, Compared["output_artifacts"]["semantic-report"])
    )
    assert Report["status"] in {"unresolved", "ambiguous", "incomplete"}
    assert (
        Report["sources"]["left"]["unresolved"]
        and Report["sources"]["right"]["unresolved"]
    )
    assert (
        Report["input_sha256"]["left"]
        == Report["input_sha256"]["right"]
        == Records["neutral_sha256"]
    )
    assert SourcePath.read_bytes() == SourceBytes
    assert not any((TmpPath / "SupervisorState/sessions").iterdir())


# forged or changed session inputs must be rejected by the independent reader worker process
@MarkValue.parametrize("ModeName", ("tamper", "fingerprint", "missing", "kit"))
def CheckRefusal(TmpPath: FilePath, ModeName: str) -> None:
    Content = (
        KRepoRoot / "re/automation/PairedCaptures" / KControls["solidworks.sldprt"]
    ).read_bytes()
    if ModeName == "kit":
        Content = BuildSldprt({KitDocStream: b"{}"})
    PinValue = DigestBytes(Content).hexdigest()
    (TmpPath / "inputs").mkdir()
    (TmpPath / "work").mkdir()
    _ = (TmpPath / "inputs" / PinValue).write_bytes(
        b"changed" if ModeName == "tamper" else Content
    )
    JobInfo = FixtureJob(
        "native-refusal",
        "reader.neutral",
        inputs={"source": "native-control"},
        depends_on=[],
        resources=[],
        options=ReaderOptions("solidworks.sldprt"),
    )
    Definition = DigestBytes(
        EncodeJson(
            JobInfo, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    InputInfo = {"binding": "native-control", "sha256": PinValue}
    Snapshot = {
        "definition_hash": Definition,
        "dependencies": {},
        "inputs": {"source": InputInfo},
    }
    Fingerprint = DigestBytes(
        EncodeJson(
            Snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()
    Descriptor = {**InputInfo, "path": f"inputs/{PinValue}"}
    if ModeName == "missing":
        del Descriptor["sha256"]
    Packet = {
        "session_version": 1,
        "job": JobInfo,
        "inputs": {"source": Descriptor},
        "dependencies": {},
        "fingerprint": "f" * 64 if ModeName == "fingerprint" else Fingerprint,
        "work": "work",
        "result": "result.json",
    }
    _ = (TmpPath / "job.json").write_text(EncodeJson(Packet), encoding="utf-8")
    Process = RunProcess(
        [
            PythonExe,
            str(KRepoRoot / "re/automation/NeutralReaderRunner.py"),
            str(TmpPath),
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert Process.returncode == 1, Process.stderr + Process.stdout
    assert not (TmpPath / "result.json").exists()
    assert not any((TmpPath / "work").iterdir())
    if ModeName == "kit":
        assert "embedded Kit documents" in Process.stderr
