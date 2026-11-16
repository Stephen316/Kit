import json as JsonCodec
import subprocess as Subprocess
import sys as System
from collections import Counter as CountItems
from pathlib import Path as FilePath
from typing import cast as CastValue


# each research record verifier runs with its own pinned archive evidence
def LoadReport(ProgramName: str) -> dict[str, object]:
    RootPath = FilePath(__file__).resolve().parents[3]
    Program = RootPath / "re/solidworks/WriterResearch" / ProgramName
    Process = Subprocess.run(
        [System.executable, str(Program)],
        cwd=RootPath,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    assert Process.returncode == 0, Process.stderr
    Report: dict[str, object] = JsonCodec.loads(Process.stdout)
    assert Report["capture_revision"] == "466dcb172dfa3803463e07ccde963ba01671d200"
    Captures = Report["captures"]
    assert isinstance(Captures, dict)
    assert len(CastValue(dict[str, str], Captures)) == 25
    return Report


# the research writer and reader must agree on the full stream in real native files
def CheckDefinition() -> None:
    Report = LoadReport("VerifyDefinition.py")
    assert Report["preamble_view_forms"] == Report["line_font_orders"] == 2


# each configuration manager record needs separate pinned evidence from the subprocess
def CheckCmgr() -> None:
    Report = LoadReport("VerifyCmgrColor.py")
    Captures = Report["captures"]
    assert isinstance(Captures, dict)
    Digests = CastValue(dict[str, str], Captures)
    assert set(Digests.values()) == {
        "3b77a4c24f8a5953b871c3b9fa7b0df54008ddf61bacb11baffc7c78fba937a9"
    }
    Terminals = Report["terminal_records"]
    assert isinstance(Terminals, dict)
    assert CastValue(dict[str, str], Terminals).keys() == Digests.keys()
    AssertEmptyMass(Report, Digests)
    AssertPartEnd(Report, Digests)
    AssertBossMass(Report, Digests)


# the empty cache must cover the complete sketch only discovery lane
def AssertEmptyMass(Report: dict[str, object], Captures: dict[str, str]) -> None:
    Masses = Report["empty_mass_records"]
    assert isinstance(Masses, dict)
    Digests = CastValue(dict[str, str], Masses)
    assert len(Digests) == 6 and Digests.keys() <= Captures.keys()
    assert set(Digests.values()) == {
        "dd69d4585ca970361fa398485ea5f2e828b0f76ebcc6b9a3ebe4287cc5cd9f31"
    }


# both saved enumeration orders must survive the hosted part reconstruction
def AssertPartEnd(Report: dict[str, object], Captures: dict[str, str]) -> None:
    Parts = Report["part_return_records"]
    assert isinstance(Parts, dict)
    Digests = CastValue(dict[str, str], Parts)
    assert Digests.keys() == Captures.keys()
    assert dict(CountItems(Digests.values())) == {
        "6bc81a35e54444c743e02c4f601f97c2d97c1ed04791355ff41f39d3021ac07a": 6,
        "ed41922d5772c1a3dd30505c22ca3560fd58329fe8fcf92930ae7ca52871001f": 8,
        "86695a925f09429c1f61fbf2a1471b42da6f8f32f1ae65cfb091253d7dae6a11": 8,
        "107161786115b59d507e01bde8b4fca38c425b4ce0f1df2cdc35dfe2456398ea": 3,
    }


# the signed boss lane needs exact option and coordinate wrapper coverage
def AssertBossMass(Report: dict[str, object], Captures: dict[str, str]) -> None:
    Masses = Report["boss_mass_wrappers"]
    assert isinstance(Masses, dict)
    Digests = CastValue(dict[str, str], Masses)
    assert len(Digests) == 8 and Digests.keys() <= Captures.keys()
    assert set(Digests.values()) == {
        "2e3fc40724bbb867dc41e0340f0b792b83d8b5cdb7254e221473c3ae1d9c73e3"
    }
