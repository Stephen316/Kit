from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

from pytest import mark as MarkValue

# the command must inspect the same checkout that owns its committed verifier sources
KRepoRoot = FilePath(__file__).resolve().parents[3]

# public replay contracts keep private evidence outside the original capture receipts
KSourcePaths = {
    "P01": "re/automation/PrincipalReadbackEvidence.py",
    "P02": "re/automation/CircleReadbackEvidence.py",
}


# manifest fixtures bind real git metadata without inventing accepted native observations
def MakeManifest(RecipeName: str = "P01") -> dict[str, object]:
    Result = RunProcess(
        ["git", "rev-parse", "HEAD"],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=True,
        timeout=15,
    )
    Revision = Result.stdout.strip()
    return {
        "version": 1,
        "scope": "paired_supplemental_preflight",
        "target_revision": Revision,
        "capture_revision": Revision,
        "frozen_rules_revision": Revision,
        "specifications_sha256": DigestBytes(
            (KRepoRoot / "re/automation/PairSpecs.json").read_bytes()
        ).hexdigest(),
        "recipes": [RecipeName],
        "evidence": [
            {
                "application": "solidworks",
                "recipe": RecipeName,
                "source_revision": Revision,
                "verifier_revision": Revision,
                "verifier_sha256": DigestBytes(
                    (KRepoRoot / KSourcePaths[RecipeName]).read_bytes()
                ).hexdigest(),
                "input_directory": "Principal",
                "input_sha256": "a" * 64,
                "report_sha256": "b" * 64,
            },
            {
                "application": "fusion",
                "recipe": RecipeName,
                "source_revision": Revision,
                "handoff_revision": "f" * 40,
            },
        ],
    }


# exact file bytes supply the independent manifest seal consumed by the real command
def WriteManifest(
    TmpPath: FilePath, Manifest: dict[str, object]
) -> tuple[FilePath, str]:
    Payload = (EncodeJson(Manifest, sort_keys=True) + "\n").encode()
    OutputPath = TmpPath / "Manifest.json"
    assert OutputPath.write_bytes(Payload) == len(Payload)
    return OutputPath, DigestBytes(Payload).hexdigest()


# each scenario crosses the standalone command boundary with a real repository checkout
def RunPreflight(
    ManifestPath: FilePath, EvidenceRoot: FilePath, Checksum: str
) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/automation/PairedEvidenceManifest.py"),
            "--manifest",
            str(ManifestPath),
            "--manifest-sha256",
            Checksum,
            "--evidence-root",
            str(EvidenceRoot),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


# an absent private report and source handoff must remain explicit nonqualification blockers
def CheckPending(TmpPath: FilePath) -> None:
    ManifestPath, Checksum = WriteManifest(TmpPath, MakeManifest())
    Result = RunPreflight(ManifestPath, TmpPath, Checksum)
    assert Result.returncode == 2, Result.stderr
    Report = ParseJson(Result.stdout)
    assert Report["status"] == "blocked"
    assert Report["qualified_pairs"] == 0
    assert Report["qualification"] == "not_evaluated"
    assert Report["manifest_sha256"] == Checksum
    assert [Entry["status"] for Entry in Report["evidence"]] == [
        "waiting_private_evidence",
        "waiting_source_handoff",
    ]
    assert Report["evidence"][1]["git_sources_available"] is False


# malformed manifests cannot alter the requested split or silently change pinned contracts
@MarkValue.parametrize(
    "FieldName,BadValue",
    [
        ("version", True),
        ("scope", "qualified"),
        ("recipes", ["P05"]),
        ("recipes", ["P01", "P01"]),
        ("specifications_sha256", "0" * 64),
        ("target_revision", "f" * 40),
        ("capture_revision", "f" * 40),
        ("frozen_rules_revision", "f" * 40),
        ("unexpected", True),
    ],
)
def CheckBadSchema(TmpPath: FilePath, FieldName: str, BadValue: object) -> None:
    Manifest = MakeManifest()
    Manifest[FieldName] = BadValue
    ManifestPath, Checksum = WriteManifest(TmpPath, Manifest)
    Result = RunPreflight(ManifestPath, TmpPath, Checksum)
    assert Result.returncode == 1
    assert not Result.stdout


# every application record must retain its exact source pins and confined private directory
@MarkValue.parametrize(
    "FieldName,BadValue",
    [
        ("application", "unknown"),
        ("recipe", "P05"),
        ("source_revision", "short"),
        ("verifier_revision", "f" * 40),
        ("verifier_sha256", "0" * 64),
        ("input_directory", "../Escape"),
        ("input_directory", "/Escape"),
        ("input_directory", "."),
        ("input_directory", "One\\Two"),
        ("report_sha256", "short"),
        ("unexpected", True),
    ],
)
def CheckBadEntry(TmpPath: FilePath, FieldName: str, BadValue: object) -> None:
    Manifest = MakeManifest()
    Entries = CastValue(list[dict[str, object]], Manifest["evidence"])
    Entries[0][FieldName] = BadValue
    ManifestPath, Checksum = WriteManifest(TmpPath, Manifest)
    Result = RunPreflight(ManifestPath, TmpPath, Checksum)
    assert Result.returncode == 1
    assert not Result.stdout


# duplicate application rows cannot stand in for missing independent vendor evidence
def CheckDuplicate(TmpPath: FilePath) -> None:
    Manifest = MakeManifest()
    Entries = CastValue(list[dict[str, object]], Manifest["evidence"])
    Entries[1] = dict(Entries[0])
    ManifestPath, Checksum = WriteManifest(TmpPath, Manifest)
    Result = RunPreflight(ManifestPath, TmpPath, Checksum)
    assert Result.returncode == 1
    assert "duplicate application and recipe" in Result.stderr


# manifests must be sealed independently rather than trusting their own parsed content
def CheckBadSeal(TmpPath: FilePath) -> None:
    ManifestPath, Checksum = WriteManifest(TmpPath, MakeManifest())
    Result = RunPreflight(ManifestPath, TmpPath, "0" * 64)
    assert Result.returncode == 1
    assert Checksum != "0" * 64
    assert "sealed input bytes changed" in Result.stderr


# oversized inputs must fail before json decoding or private evidence replay
def CheckSizeLimit(TmpPath: FilePath) -> None:
    Payload = b" " * (1024 * 1024 + 1)
    ManifestPath = TmpPath / "Manifest.json"
    assert ManifestPath.write_bytes(Payload) == len(Payload)
    Result = RunPreflight(ManifestPath, TmpPath, DigestBytes(Payload).hexdigest())
    assert Result.returncode == 1
    assert "byte limit" in Result.stderr


# linked private evidence cannot redirect a replay outside the selected custody root
def CheckInputLink(TmpPath: FilePath) -> None:
    OutsidePath = TmpPath / "Outside"
    OutsidePath.mkdir()
    (TmpPath / "Principal").symlink_to(OutsidePath, target_is_directory=True)
    ManifestPath, Checksum = WriteManifest(TmpPath, MakeManifest())
    Result = RunPreflight(ManifestPath, TmpPath, Checksum)
    assert Result.returncode == 1
    assert "plain files and directories" in Result.stderr


# linked manifests cannot move the independently sealed input behind the operator
def CheckSealLink(TmpPath: FilePath) -> None:
    ManifestPath, Checksum = WriteManifest(TmpPath, MakeManifest())
    LinkedPath = TmpPath / "Linked.json"
    LinkedPath.symlink_to(ManifestPath)
    Result = RunPreflight(LinkedPath, TmpPath, Checksum)
    assert Result.returncode == 1
    assert "plain files and directories" in Result.stderr


# a copied normalized report never substitutes for the original native receipt chain
@MarkValue.parametrize("RecipeName", ["P01", "P02"])
def CheckRawProof(TmpPath: FilePath, RecipeName: str) -> None:
    Manifest = MakeManifest(RecipeName)
    Payload = EncodeJson({"schema": 1, "qualification": False}).encode()
    PrivatePath = TmpPath / "Principal"
    PrivatePath.mkdir()
    RecordName = "receipt.json" if RecipeName == "P02" else "dispatch.json"
    assert (PrivatePath / RecordName).write_bytes(Payload) == len(Payload)
    Entries = CastValue(list[dict[str, object]], Manifest["evidence"])
    Entries[0]["input_sha256"] = DigestBytes(Payload).hexdigest()
    ManifestPath, Checksum = WriteManifest(TmpPath, Manifest)
    Result = RunPreflight(ManifestPath, TmpPath, Checksum)
    assert Result.returncode == 1
    assert not Result.stdout
    assert "raw-chain verifier refused" in Result.stderr


# duplicate json keys cannot make the operator and verifier read different manifests
def CheckJsonKeys(TmpPath: FilePath) -> None:
    Payload = b'{"version": 1, "version": 2}'
    ManifestPath = TmpPath / "Manifest.json"
    assert ManifestPath.write_bytes(Payload) == len(Payload)
    Result = RunPreflight(ManifestPath, TmpPath, DigestBytes(Payload).hexdigest())
    assert Result.returncode == 1
    assert "duplicate JSON key" in Result.stderr


# raw record links remain forbidden even when the enclosing private directory is plain
def CheckRecordLink(TmpPath: FilePath) -> None:
    ManifestPath, Checksum = WriteManifest(TmpPath, MakeManifest())
    PrivatePath = TmpPath / "Principal"
    PrivatePath.mkdir()
    (PrivatePath / "dispatch.json").symlink_to(ManifestPath)
    Result = RunPreflight(ManifestPath, TmpPath, Checksum)
    assert Result.returncode == 1
    assert "plain files and directories" in Result.stderr
