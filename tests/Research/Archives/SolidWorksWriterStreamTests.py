import json as JsonCodec
import subprocess as Subprocess
import sys as System
from collections import Counter as CountItems
from hashlib import sha256 as DigestBytes
from pathlib import Path as FilePath
from typing import cast as CastValue


# each research record verifier runs with its own pinned archive evidence
def LoadReport(ProgramName: str, CaptureCount: int = 25) -> dict[str, object]:
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
    assert len(CastValue(dict[str, str], Captures)) == CaptureCount
    return Report


# the authored profile opening must transfer its owned sketch and point count
def CheckProfile() -> None:
    Report = LoadReport("VerifyAuthoredProfile.py", 14)
    assert Report["constructed"] is True
    assert Report["nonzero_regen_times"] == 2
    assert (
        Report["replay_sha256"]
        == "94e7a495ed5aab2ba98e8833c5154869c0d0678dc778e8ef2387d7b83b189156"
    )
    assert (
        Report["corner_replay_sha256"]
        == "824ef34e99d0bd6f0aa4b5d92cbc5532b296fd1f14e8590438135cfcdba540c8"
    )


# the research writer and reader must agree on the full stream in real native files
def CheckDefinition() -> None:
    Report = LoadReport("VerifyDefinition.py")
    assert Report["preamble_view_forms"] == Report["line_font_orders"] == 2


# the resolved folder sequence must retain the real feature and archive identities
def CheckResFolder() -> None:
    Report = LoadReport("VerifyResolvedFolders.py", 14)
    Encoded = JsonCodec.dumps(Report["captures"], sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "21a06cba04c78d1311519d08df37d3dc310cf090075a6916abc371fd93fd583e"
    )
    Cabinets = Report["cabinet_records"]
    assert isinstance(Cabinets, dict) and len(CastValue(dict[str, str], Cabinets)) == 14
    Encoded = JsonCodec.dumps(Cabinets, sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "8ab5fe560c589276e8cf2a548c5b22e9d29dbe1f81bd0150d9ec47f645a67a05"
    )
    LaterFolders = Report["late_folder_records"]
    assert isinstance(LaterFolders, dict) and LaterFolders.keys() == Cabinets.keys()
    Encoded = JsonCodec.dumps(LaterFolders, sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "d7cd9e7f9f20eb1a8eafbf46e7ccfc4a0dabb51dfc60c6b399e19a6264c8d61f"
    )


# each default plane must preserve its class allocation and measured presentation
def CheckResPlanes() -> None:
    Report = LoadReport("VerifyResolvedPlanes.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "58ea10925023d080a670a3e10884043677ad584cca704864f52a47860bea86c2"
    )
    OriginRecords = Report["origin_records"]
    assert isinstance(OriginRecords, dict) and len(OriginRecords) == 14
    Encoded = JsonCodec.dumps(OriginRecords, sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "591a9357a828d8dff9e062896cf3478d366f3aa084b0f10a6ac28c74aefcad81"
    )


# the configured model title must keep real allocation order in the standalone archive
def CheckConfigRoot() -> None:
    Report = LoadReport("VerifyConfigRoot.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "b73087297e042f37f9bb4d9b87f54ae02aedd9407da1002cb31229a56de5f933"
    )


# each configuration visual owner must agree with the separately saved material body
def CheckConfigVis() -> None:
    Report = LoadReport("VerifyConfigVisual.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "4fa9ad81435c8a0231ce0f280e62b29648dffa409d9be17e621bc73584aec82b"
    )


# unit selectors and earlier length values must keep their separate saved fields
def CheckConfigUnit() -> None:
    Report = LoadReport("VerifyConfigUnits.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "8c4195e8660da7a1751a8c1c3d5c4e35ad53b2e58bfa6e8d9137fd36b3999a37"
    )


# both optional curvature branches must retain their native model and plane allocation
def CheckConfigView() -> None:
    Report = LoadReport("VerifyConfigView.py", 14)
    assert Report["constructed"] is True
    assert Report["curvature_records"] == 8
    assert (
        Report["replay_sha256"]
        == "55dc06d858890565b1422363d76a22c12fde4e88c2bd573edf7ff559c6702569"
    )


# material handoff must retain actual ownership across both model box branches
def CheckConfigBody() -> None:
    Report = LoadReport("VerifyConfigBody.py", 14)
    assert Report["constructed"] is True
    assert Report["model_boxes"] == 8
    assert (
        Report["replay_sha256"]
        == "ef3be3962d274b830225cc91c447269c7b946147ec0811fe8364852f69890bdf"
    )


# material and definition must agree on density before the model data allocation
def CheckConfigMat() -> None:
    Report = LoadReport("VerifyConfigMat.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "f7f43f4bbee7452e83d0fd271eaf6143b49bc9453556310cc4bb1119aa7f09ce"
    )


# the same typed writer must reach both native split boundaries with its live map
def CheckCfgSplits() -> None:
    Report = LoadReport("VerifyConfigSplitEdges.py", 14)
    assert (
        Report["replay_sha256"]
        == "4dc6ac3465879123e0271e20a88ac585652414ba86f531243b37a442c52292c3"
    )


# the atom binding must follow both the independent map and native boss owner
def CheckCfgAtoms() -> None:
    Report = LoadReport("VerifyConfigAtoms.py", 14)
    assert (
        Report["replay_sha256"]
        == "193129f1559b395334b21a75f00b49ccf19f343b83ccb95ce63bdab175d83865"
    )


# inline ghost state and the relation allocation must close at saved detail
def CheckGhostRel() -> None:
    Report = LoadReport("VerifyConfigGhostRelation.py", 14)
    assert (
        Report["replay_sha256"]
        == "0ba2e2768dbbe1c6bba1e669fdde413b75edba4e4819b4a7f0e17e77ba8fba23"
    )


# authored log order and shared archive allocation must survive repeated edits
def CheckModelHdr() -> None:
    Report = LoadReport("VerifyModelHeader.py")
    Encoded = JsonCodec.dumps(Report["captures"], sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "3028ee71641c89df6c79c88c8bc299e464ad7c00d563c1396e751ac906554636"
    )
    Records = Report["model_header_records"]
    assert isinstance(Records, dict)
    assert len(CastValue(dict[str, str], Records)) == 25
    Encoded = JsonCodec.dumps(Records, sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "d577d96774b072bef17a237fc13a39eb1b876531bd52a5782df53b1821bd6787"
    )


# the detail opening and font must retain their native intervals and archive map
def CheckCfgDetail() -> None:
    Report = LoadReport("VerifyConfigDetail.py", 14)
    assert (
        Report["replay_sha256"]
        == "28ca63bc7a3bfd1f64917d471b2bb2146c477a0d4ebf15276ff4effc9ab7e0c8"
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
    AssertMgrHdr(Report)


# header bookkeeping and saved body counts must retain their independent evidence
def AssertMgrHdr(Report: dict[str, object]) -> None:
    Links = Report["linked_atom_records"]
    Headers = Report["base_header_records"]
    Fronts = Report["collection_front_records"]
    Tails = Report["collection_tail_records"]
    Composed = Report["composed_cmgr_records"]
    assert isinstance(Links, dict)
    assert isinstance(Headers, dict)
    assert isinstance(Fronts, dict)
    assert isinstance(Tails, dict)
    assert isinstance(Composed, dict)
    assert (
        Links.keys()
        == Headers.keys()
        == Fronts.keys()
        == Tails.keys()
        == Composed.keys()
    )
    FrontDigests = CastValue(dict[str, str], Fronts)
    assert dict(CountItems(FrontDigests.values())) == {
        "ae538a3e846dc88c0dbc655355665826638036d85c799e299f2dd1e2a50c25e7": 6,
        "c78f21f350ce049a9a155ece4aff10eff8bf65561bb0579d6d8a88a1962811cc": 8,
    }
    TailDigests = CastValue(dict[str, str], Tails)
    assert dict(CountItems(TailDigests.values())) == {
        "131d69a783db2ff24e0472f8fc1f50693dd8a70964923e677d2c23c71360ba70": 6,
        "9c1a8d14af8536db4e4c6dff00cdbc65aae27783666bea612fef32b3432d2aee": 8,
    }
    Encoded = JsonCodec.dumps(Headers, sort_keys=True, separators=(",", ":"))
    assert (
        DigestBytes(Encoded.encode("ascii")).hexdigest()
        == "27cc75de0930610b2681d28ed10e6cc597f551532aad3854bb0089829a91de5d"
    )


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
