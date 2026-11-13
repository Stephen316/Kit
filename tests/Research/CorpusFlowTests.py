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
            Manifest.write_text(JsonCodec.dumps(Payload), encoding="utf-8")
        Checked = Subprocess.run(
            Command
            + ["check", "--manifest", str(Manifest)]
            + (["--require-pairs"] if CaseMode == "pairs-required" else []),
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    assert (
        Checked.returncode
        == {"intact": 0, "tampered": 1, "pairs-required": 2}[CaseMode]
    ), Checked.stderr
