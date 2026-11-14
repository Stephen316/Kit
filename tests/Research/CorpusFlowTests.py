import json as JsonCodec
import subprocess as Subprocess
import sys as System
import tempfile as TempFiles
from pathlib import Path as FilePath

import pytest as Pytest


@Pytest.mark.parametrize("CaseMode", ("intact", "tampered", "pairs-required"))
def CheckCorpusFlow(CaseMode: str) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Revision = Subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=RootPath, text=True
    ).strip()
    Command = [System.executable, str(RootPath / "re/automation/Corpus.py")]
    with TempFiles.TemporaryDirectory() as TempPath:
        Manifest = FilePath(TempPath) / "Corpus.json"
        Created = Subprocess.run(
            Command + ["snapshot", "--revision", Revision, "--manifest", str(Manifest)],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        assert Created.returncode == 0, Created.stderr
        Payload = JsonCodec.loads(Manifest.read_text(encoding="utf-8"))
        assert Payload["summary"]["native_by_format"]["sldprt"] > 0
        assert Payload["summary"]["native_by_format"]["f3d"] > 0
        if CaseMode == "tampered":
            Payload["assets"][0]["sha256"] = "0" * 64
            _ = Manifest.write_text(JsonCodec.dumps(Payload), encoding="utf-8")
        Checked = Subprocess.run(
            Command
            + ["check", "--manifest", str(Manifest)]
            + (["--require-pairs"] if CaseMode == "pairs-required" else []),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    ExpectedCode, ExpectedMessage = {
        "intact": (0, ""),
        "tampered": (1, "manifest differs from pinned Git objects"),
        "pairs-required": (2, "blocked: independently authored"),
    }[CaseMode]
    assert Checked.returncode == ExpectedCode, Checked.stderr
    assert ExpectedMessage in Checked.stderr, Checked.stderr


@Pytest.mark.parametrize("RequirePairs", (False, True))
def CheckPairIntake(RequirePairs: bool) -> None:
    RootPath = FilePath(__file__).resolve().parents[2]
    Revision = Subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=RootPath, text=True
    ).strip()
    Command = [
        System.executable,
        str(RootPath / "re/automation/PairedCaptureIntake.py"),
        "--revision",
        Revision,
    ]
    if RequirePairs:
        Command.append("--require-pairs")
    Result = Subprocess.run(
        Command, cwd=RootPath, capture_output=True, text=True, check=False, timeout=120
    )
    assert Result.returncode == (2 if RequirePairs else 0), Result.stderr
    Report = JsonCodec.loads(Result.stdout)
    assert Report["source_revision"] == Revision
    assert Report["quarantined_families"] == []
    assert Report["summary"] == {
        "paired_recipes": 5,
        "capture_receipts": 10,
        "native_files": 74,
        "native_files_by_reserved_split": {
            "discovery": 50,
            "qualification": 10,
            "holdout": 14,
        },
        "qualified_pairs": 0,
        "blocked_recipes": ["P01", "P02", "P03", "P04", "P05"],
    }
    AssertPairRules(Report)


def AssertPairRules(Report: dict[str, object]) -> None:
    Captures = JsonCodec.loads(JsonCodec.dumps(Report["captures"]))
    assert len({(Entry["recipe_id"], Entry["application"]) for Entry in Captures}) == 10
    for Capture in Captures:
        if Capture["recipe_id"] == "P05":
            assert Capture["permitted_use"] == "holdout_with_frozen_rules"
        elif Capture["recipe_id"] == "P02":
            assert Capture["permitted_use"] == "qualification_with_frozen_rules"
        else:
            assert Capture["permitted_use"] == "discovery"
        Coverage = Capture["recording_coverage"]
        Blockers = Capture["qualification_blockers"]
        if Capture["application"] == "fusion":
            assert Coverage["missing_readbacks"] == ["baseline-b"]
            assert Coverage["clean_load_diagnostic_count"] == 0
            assert "fresh_application_process_unrecorded" in Blockers
        else:
            assert Coverage["missing_readbacks"] == []
            assert Coverage["clean_load_diagnostic_count"] == len(
                Capture["native_files"]
            )
            assert (
                Capture["provenance"]["generator_status"] == "retained_audited_source"
            )
            assert "authoring_harness_not_pinned" not in Blockers
        assert ("supporting_face_identity_unrecorded" in Blockers) == (
            Capture["recipe_id"] == "P04"
        )
