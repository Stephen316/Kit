# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from datetime import datetime as Timestamp
from pathlib import Path as FilePath
from re import fullmatch as FullMatch

from Corpus import git as ReadGit
from PairedCaptureIntake import require as RequirePad, sha256 as ShaValue
from PilotEvidence import checksum as HasSha, pinned_record as ReadJsonPin

# the stock bytes and all compiled capture inputs have fixed repository identities
KSourceFolder = "re/automation/PairedCaptures/SolidWorksAuthoring"

# the stock control is identified by the same path as the captured collector
KStockPath = "re/solidworks/examples/.SLDPRT/example.SLDPRT"

# the compiled source roster can be verified independently from the observed run
KSourcePaths = (
    f"{KSourceFolder}/RunTwoPad.ps1",
    f"{KSourceFolder}/TwoPadCapture.cs",
    f"{KSourceFolder}/SolidWorksCapture.cs",
    f"{KSourceFolder}/TwoPadComSession.cs",
    "re/automation/PairSpecs.json",
    KStockPath,
)

# aggregate evidence binds the independently authored second baseline to the reopen phase
KVariants = ("baseline-a", "depth-3", "depth-8", "support-11", "baseline-b")

# the authoring phase must agree on the part saved before any reopen
KAuthoredKeys = ("variant", "base_depth_mm", "upper_depth_mm", "authored", "save")

# both native processes require a bracket of stock controls
KPhases = ("authoring", "reopen")


# retain only regular local archives whose contents match the supplied receipt
def ReadPadBytes(Directory: FilePath, FileName: str, Digest: str) -> bytes:
    PathValue = Directory / FileName
    RequirePad(
        PathValue.is_file() and PathValue.resolve() == PathValue,
        f"Expected a direct local file: {FileName}",
    )
    with PathValue.open("rb") as Stream:
        DataValue = Stream.read(32 * 1024 * 1024 + 1)
    RequirePad(
        len(DataValue) <= 32 * 1024 * 1024,
        f"Archive exceeds evidence limit: {FileName}",
    )
    RequirePad(
        HasSha(Digest) and ShaValue(DataValue) == Digest,
        f"Archive SHA-256 mismatch: {FileName}",
    )
    return DataValue


# the report must use the exact capture source and original stock from the trusted revision
def CheckSources(RepoRoot: FilePath, Revision: str, Report: dict) -> str:
    RequirePad(
        FullMatch("[0-9a-f]{40}", Revision) is not None,
        "Expected a full capture source revision",
    )
    RequirePad(
        ReadGit(RepoRoot, "rev-parse", "--verify", f"{Revision}^{{commit}}")
        .decode()
        .strip()
        == Revision,
        "The trusted revision is not the exact Git commit",
    )
    Expected = {
        PathText: ShaValue(
            ReadGit(RepoRoot, "cat-file", "blob", f"{Revision}:{PathText}")
        )
        for PathText in KSourcePaths
    }
    RequirePad(
        type(Report["schema"]) is int
        and Report["schema"] == 1
        and Report["scope"] == "solidworks-face-supported-two-pad-discovery"
        and Report["source_revision"] == Revision
        and Report["sources"] == Expected,
        "Report scope or capture source pins differ from the trusted commit",
    )
    Installed = Report["installed_files"]
    RequirePad(
        set(Installed) == {"executable", "interop", "constants"}
        and all(map(HasSha, Installed.values())),
        "Malformed installed application identities",
    )
    return Expected[KStockPath]


# the recorded native process and exit receipt must bind the same verified phase archive
def ReadPadPhase(
    Directory: FilePath, Report: dict, PhaseName: str, PhaseSha: str
) -> tuple[dict, dict]:
    RunValue = Report["observations"][f"{PhaseName}_process"]
    OwnerSha = RunValue["owner_sha256"]
    ExitSha = RunValue["exit_receipt_sha256"]
    Owner = ReadJsonPin(Directory / f"{PhaseName}-owner.json", OwnerSha)
    ExitValue = ReadJsonPin(Directory / f"{PhaseName}-exit.json", ExitSha)
    Measures = ReadJsonPin(Directory / f"{PhaseName}-measurements.json", PhaseSha)
    ProcessId = Owner["pid"]
    RequirePad(
        Owner["phase"] == PhaseName
        and type(ProcessId) is int
        and ProcessId > 0
        and type(Owner["session_id"]) is int
        and Owner["session_id"] > 0
        and type(Owner["initial_documents"]) is int
        and Owner["initial_documents"] == 0
        and isinstance(Owner["created_filetime"], str)
        and Owner["created_filetime"].isdecimal()
        and int(Owner["created_filetime"]) > 0
        and Timestamp.fromisoformat(Owner["started_utc"]).tzinfo is not None
        and Owner["executable_sha256"] == Report["installed_files"]["executable"]
        and Owner["application_build"] == Report["application_build"]
        and isinstance(Owner["resolved_executable"], str)
        and bool(Owner["resolved_executable"]),
        f"Invalid owned process identity: {PhaseName}",
    )
    RequirePad(
        ExitValue["exited_observed"] is True
        and type(ExitValue["exit_code"]) is int
        and ExitValue
        == {
            "phase": PhaseName,
            "pid": ProcessId,
            "exited_observed": True,
            "owner_sha256": OwnerSha,
            "measurements_sha256": PhaseSha,
            "exit_code": 0,
            "exit_hex": "0x00000000",
        },
        f"Native exit receipt does not bind a successful phase: {PhaseName}",
    )
    ObservedOwner = {**Owner, "owner_sha256": OwnerSha}
    RequirePad(
        Measures[f"{PhaseName}_process"] == ObservedOwner
        and RunValue
        == {
            **ObservedOwner,
            "measurements_sha256": PhaseSha,
            "exit_receipt_sha256": ExitSha,
            "exited_observed": True,
            "exit_code": 0,
        },
        f"Aggregate report does not bind the owned phase archive: {PhaseName}",
    )
    return Owner, Measures


# the report must close the unedited save and reopen chain against both independent receipts
def CheckPhases(
    Directory: FilePath, Report: dict, AuthorSha: str, ReopenSha: str
) -> tuple[int, int]:
    First, Authoring = ReadPadPhase(Directory, Report, "authoring", AuthorSha)
    Second, Reopened = ReadPadPhase(Directory, Report, "reopen", ReopenSha)
    RequirePad(
        First["pid"] != Second["pid"]
        and First["session_id"] == Second["session_id"]
        and First["resolved_executable"] == Second["resolved_executable"]
        and int(First["created_filetime"]) < int(Second["created_filetime"])
        and Timestamp.fromisoformat(First["started_utc"])
        < Timestamp.fromisoformat(Second["started_utc"]),
        "Reopen did not use a newer independent native process on the same desktop",
    )
    Observations = Report["observations"]
    Cases = Observations["cases"]
    RequirePad(
        tuple(CaseValue["variant"] for CaseValue in Cases) == KVariants,
        "Unexpected discovery roster",
    )
    RequirePad(
        {**Reopened, "reopen_process": Observations["reopen_process"]} == Observations
        and Authoring
        == {
            "authoring_process": {
                **First,
                "owner_sha256": Observations["authoring_process"]["owner_sha256"],
            },
            "authoring_control_before": Observations["authoring_control_before"],
            "authoring_control_after": Observations["authoring_control_after"],
            "cases": [
                {KeyName: CaseValue[KeyName] for KeyName in KAuthoredKeys}
                for CaseValue in Cases[:-1]
            ],
        },
        "The aggregate report does not reproduce the authored inputs and the separate reopen archive",
    )
    return First["pid"], Second["pid"]
