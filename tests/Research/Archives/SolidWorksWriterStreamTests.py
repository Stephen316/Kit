import json as JsonCodec
import subprocess as Subprocess
import sys as System
from collections import Counter as CountItems
from hashlib import sha256 as DigestBytes
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


# authored log order and shared archive allocation must survive repeated edits
def CheckModelHdr() -> None:
    Report = LoadReport("VerifyModelHeader.py")
    Encoded = JsonCodec.dumps(Report["captures"], sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "3028ee71641c89df6c79c88c8bc299e464ad7c00d563c1396e751ac906554636"
    )


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
    AssertExtFile(Report, Digests)
    AssertEmptyMass(Report, Digests)
    AssertPartEnd(Report, Digests)
    AssertBossMass(Report, Digests)
    AssertAtomLinks(Report, Digests)
    AssertCmgrEnds(Report)


# both path forms must preserve the saved metadata of each capture
def AssertExtFile(Report: dict[str, object], Captures: dict[str, str]) -> None:
    Records = Report["external_file_records"]
    assert isinstance(Records, dict)
    Digests = CastValue(dict[str, str], Records)
    assert Digests.keys() == Captures.keys()
    Encoded = JsonCodec.dumps(Digests, sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "821c4d8dfda184b6641892ff54b6133a39a536f62aef3022f8097a05be033654"
    )


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


# the two supported histories need distinct link maps and exact hosted coverage
def AssertAtomLinks(Report: dict[str, object], Captures: dict[str, str]) -> None:
    Links = Report["linked_atom_records"]
    assert isinstance(Links, dict)
    Digests = CastValue(dict[str, str], Links)
    assert Digests.keys() <= Captures.keys()
    assert dict(CountItems(Digests.values())) == {
        "df3f619804a92fdb4057192dc43dd748ea778adc52bc498ce80524c014b81119": 6,
        "22f5e73e80dea9ff154f1cb37127fc677648b8796824d1c6d17ddd711a5ac4fb": 8,
    }


# the base return and aliases must cover the same captures as independent links
def AssertCmgrEnds(Report: dict[str, object]) -> None:
    Links = Report["linked_atom_records"]
    assert isinstance(Links, dict)
    LinkDigests = CastValue(dict[str, str], Links)
    for Section, Digest in (
        (
            "base_return_records",
            "09c4b9259191e2551e2113b623f9835dfdcb061e534ec0f74920cc6e56bd5890",
        ),
        (
            "manager_alias_records",
            "e5f9b36d163ace0f12265dcf7e98bbbfc5637a79dcfefcbe3e945f14ca9833f6",
        ),
    ):
        Records = Report[Section]
        assert isinstance(Records, dict)
        Digests = CastValue(dict[str, str], Records)
        assert Digests.keys() == LinkDigests.keys()
        assert set(Digests.values()) == {Digest}
