import json as JsonCodec
import subprocess as Subprocess
import sys as System
from collections import Counter as CountItems
from hashlib import sha256 as DigestBytes
from pathlib import Path as FilePath
from typing import cast as CastValue


# each research record verifier runs with its own pinned archive evidence
def LoadReport(
    ProgramName: str,
    CaptureCount: int = 25,
    CaptureRevision: str = "466dcb172dfa3803463e07ccde963ba01671d200",
) -> dict[str, object]:
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
    assert Report["capture_revision"] == CaptureRevision
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
    assert (
        Report["proxy_replay_sha256"]
        == "422534f2ef8bd02ecb8f71c4d0bd6a7b7618dc4b15c5c9a6ab1db3d88bc2dc79"
    )
    assert Report["line_mark_orders"] == 2
    assert (
        Report["line_replay_sha256"]
        == "8fc41b75f4c3b0bd5e0e35a3285cc835f47f8e99a0716aa53722c26258fe97cc"
    )
    assert (
        Report["dim_replay_sha256"]
        == "f20f6992915f75a45303b854e80e73d2d953409896ed3d162dc234beb9ab4a71"
    )
    assert (
        Report["axis_replay_sha256"]
        == "22e2a564d8acabb259e39fdafa8117f92f674f3e9dc78890558e91aa5616a2c1"
    )
    assert (
        Report["anchor_replay_sha256"]
        == "911a547d6a70f2ab633be265d29c0b2a43672439e6564c21989eae676ca3a53b"
    )
    assert (
        Report["display_replay_sha256"]
        == "c2b3cc8dcd6445c9650372c4321b76d063794a50d97ebdc7d3a5931546658878"
    )
    assert (
        Report["region_replay_sha256"]
        == "62ed618ff67a5f2a03b75398ef86152d16e7c9b85830a59f7f28973b4a398901"
    )
    assert (
        Report["support_replay_sha256"]
        == "657ee948b0103e209898b259f1be7d1df580312c61afedd7deb3b01ceb6ca75d"
    )
    assert (
        Report["trim_replay_sha256"]
        == "772dc555b6cfbe4264ca8701b15da6787d881f3496457c2c816953fb13bf511c"
    )


# the trimmed profile must return its shared file allocation with all side members intact
def CheckRectTrim() -> None:
    Report = LoadReport("VerifyRectTrim.py", 14)
    assert Report["constructed"] is True
    assert Report["path_forms"] == 2
    assert Report["side_orders"] == 4
    assert Report["extrusion_returns"] == 8
    assert (
        Report["trim_replay_sha256"]
        == "772dc555b6cfbe4264ca8701b15da6787d881f3496457c2c816953fb13bf511c"
    )


# the first extrusion must carry the same profile and configuration owners into its chooser
def CheckBossOpen() -> None:
    Report = LoadReport("VerifyBossOpen.py", 8)
    assert Report["constructed"] is True
    assert Report["reverse_directions"] == 1
    assert Report["nonzero_regen_times"] == 1
    assert (
        Report["opening_replay_sha256"]
        == "43415df07de102cfb940542ade9ecf91df9afee9f4b24f39dfd4366b69a288ce"
    )


# genuine chooser references must distinguish first allocations and later cap aliases
def CheckBossChoice() -> None:
    Report = LoadReport("VerifyBossChoice.py", 8)
    assert Report["constructed"] is True
    assert Report["edge_orders"] == 2
    assert Report["stale_boxes"] == 3
    assert (
        Report["choice_replay_sha256"]
        == "bd4477321aea633bfb06579621443054a0bdefc134b081195d413b4fbef1f2a6"
    )


# the signed end enters the existing distance display after the native partition marker
def CheckBossEnd() -> None:
    Report = LoadReport("VerifyBossEndOpen.py", 8)
    assert Report["constructed"] is True
    assert Report["mark_ids"] == [7, 9, 11, 15, 19, 23]
    assert Report["reverse_directions"] == 1
    assert (
        Report["end_open_replay_sha256"]
        == "209520b1305788589d2d235f784f66d8ff8642b327d027ef43df22b9964a3343"
    )


# composition must reach exact eof with one named driving depth and archive map
def CheckBossWhole() -> None:
    Report = LoadReport("VerifyBossResolve.py", 8)
    assert Report["constructed"] is True
    assert Report["saved_property_forms"] == 3
    assert (
        Report["boss_replay_sha256"]
        == "b90d5aa693f33eed082fc9250cf78bb79f54a545a22859f67ce714041eb74eab"
    )


# paired discovery keeps its admission refusal while an authored neutral graph maps
def CheckBossInput() -> None:
    Report = LoadReport(
        "VerifyBossInput.py", 8, "89c25945f5833ad9c3a1c6c683df510b5702dd54"
    )
    assert Report["authored_cases"] == [[3, 37.5, 18.25, 13.5], [1, 42.25, 17.5, -8.75]]
    assert (
        Report["paired_sha256"]
        == "f08dc5bb81e474b536611b4c96d1f58f42d1fc642e8c6725730c2cbbe8bda648"
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
    assert (
        isinstance(OriginRecords, dict)
        and len(CastValue(dict[str, object], OriginRecords)) == 14
    )
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


# the standard view group preserves its generated camera bases and archive allocations
def CheckCfgViews() -> None:
    Report = LoadReport("VerifyConfigSavedViews.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["environment_sha256"]
        == "c4acd833de3c4ad561983b6f6896e22a311ca0827e29311f8a0b6bf49536d1d8"
    )
    assert (
        Report["replay_sha256"]
        == "56fbc3f5a09c81918a8702d5598172b3c4650aba233901e3ddf293073abee395"
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


# the composed prefix must carry the first split map through saved detail entry
def CheckCfgHistory() -> None:
    Report = LoadReport("VerifyConfigHistory.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "37aaf6279b6d66aee9e03cfad8e35346caeeb98739573d03384938827619eb91"
    )


# the generated part configuration must reach the exact end and resolve aliases
def CheckCfgArchive() -> None:
    Report = LoadReport("VerifyOrdinaryConfig.py", 14)
    assert Report["constructed"] is True
    assert (
        Report["replay_sha256"]
        == "7f6ab4f42ab1d06ced9d90a23683eb092f34ad1856ea48f4b4a2100d50f7c812"
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


# the full detail start and its independent subrecords must preserve native ownership
def CheckCfgDetail() -> None:
    Report = LoadReport("VerifyConfigDetail.py", 14)
    assert (
        Report["replay_sha256"]
        == "49e99ba22e662e41ba7895895cad5f14f5095039430f1b755492030b0ca00dd7"
    )


# the dimension styles must preserve native unit ownership and the annotation boundary
def CheckDimStyles() -> None:
    Report = LoadReport("VerifyDimensionStyles.py", 14)
    assert (
        Report["replay_sha256"]
        == "5fe2c5a1d827b0eecd71310587752b208a99201a5f1891d4f62e5470ca83312e"
    )


# annotation definitions must reach the table boundary without new archive objects
def CheckCfgAnno() -> None:
    Report = LoadReport("VerifyConfigAnnotations.py", 14)
    assert (
        Report["replay_sha256"]
        == "c70e99640be3231a0239d84e64203b5af1f7be90e89129b9fbb924c1a9dc0b07"
    )


# the table settings must reach the native label boundary with the same archive map
def CheckCfgTables() -> None:
    Report = LoadReport("VerifyConfigTables.py", 14)
    assert (
        Report["replay_sha256"]
        == "b3d0a77dc2f93a84c3509b254d954090b96968c8db4232cbab350e8fbc6339a3"
    )


# the drawing labels must reach the native surface finish boundary with the same map
def CheckCfgLabels() -> None:
    Report = LoadReport("VerifyConfigLabels.py", 14)
    assert (
        Report["replay_sha256"]
        == "ec01b43a07347fac6f8e851b419a03da1a6cd70bab391a3ba90a0d392e9443d1"
    )


# the finish and note definitions must reach the weld helper without allocations
def CheckCfgHelpers() -> None:
    Report = LoadReport("VerifyConfigFinishNote.py", 14)
    assert (
        Report["replay_sha256"]
        == "2ceee3fcf4ba3de8a4a94aa881bebc97dddd865a246631912053b1c7c04ed70f"
    )


# the weld and tolerance helpers must preserve native frames and archive ownership
def CheckCfgWeldTol() -> None:
    Report = LoadReport("VerifyConfigWeldTolerance.py", 14)
    assert (
        Report["weld_replay_sha256"]
        == "2115ff0916fd90b17900e6bba2c67ce9964183de9c3e446197bf8b93d3791a0b"
    )
    assert (
        Report["tolerance_replay_sha256"]
        == "7e2e03da49c28147edfe34010635b41553073c2ceaf74c859a450f9de11c6360"
    )


# the final detail settings must hand off to the native environment with the same map
def CheckDetailEnd() -> None:
    Report = LoadReport("VerifyConfigDetailEnd.py", 14)
    assert (
        Report["replay_sha256"]
        == "3b099160e1ab5803a6a4d06712abe98aebbec950fef8dc5943c8a2647ad0429a"
    )


# the complete saved detail must reproduce the native span and map
def CheckDetailMap() -> None:
    Report = LoadReport("VerifyConfigDetailComposition.py", 14)
    assert (
        Report["replay_sha256"]
        == "11a50a77b4c25deb5cfad5cc88fb3e0efe637d1d284d3550ebd36de06c721310"
    )


# exact sidecar bytes and retained member names should agree across the eight licensed saves
def CheckSidecars() -> None:
    Report = LoadReport("VerifyPartSidecars.py", 8)
    assert (
        Report["replay_sha256"]
        == "a0361c2da1f1182d8976fbabe0d77eaa9579dccfa6655554b622c2485ac36cd9"
    )
    assert (
        Report["package_sha256"]
        == "865e7d717d4d4fff91c1df314e3cd1895b03f2a8bda4cfe9a8346fec12c2251e"
    )
    assert (
        Report["document_sha256"]
        == "76446501f05f8a0087064f6023170f518ca07dc7e795443c03da32427b03fb7f"
    )
    assert (
        Report["retained_sha256"]
        == "f9e2742038653d48e89f4eef3bfd6f8c17846d4a3b4d8b8dd84fb78c9b0dcfb5"
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


# the generated block must retain exact map ownership through the annotation list
def CheckSkBlock() -> None:
    Report = LoadReport("VerifySketchBlock.py", 14)
    assert Report["map_counts"] == {"94:96:99": 6, "98:100:104": 8}


# annotated cardinal views must retain exact basis bits and the following archive map
def CheckCfgAnnots() -> None:
    Report = LoadReport("VerifyConfigAnnotViews.py", 14)
    assert Report["span_counts"] == {"214": 5, "286": 1, "470": 7, "542": 1}
    assert (
        Report["replay_sha256"]
        == "8a2cec83cdf5292b293cab777f8c11290a5b477c9bfb7a090158e51a2fabfc9d"
    )


# the native marker and thread allocations must leave the following model regions readable
def CheckCfgLists() -> None:
    Report = LoadReport("VerifyCfgModelLists.py", 14)
    assert (
        Report["replay_sha256"]
        == "6c8aa5c122c06bb984a2bd519c74a5c0d2d165f34586c7c07ace6dee98154da0"
    )


# the generated cache brackets and manager must leave the exact resolved archive map
def CheckCfgEnd() -> None:
    Report = LoadReport("VerifyCfgPartEnd.py", 14)
    assert (
        Report["replay_sha256"]
        == "cd16fa11ca352bbc39545ff7c5d8c3afd78f4bdc61ef611cc1f92150c39c8e34"
    )


# full native manifests must bind the three standard property targets
def CheckManifests() -> None:
    Report = LoadReport("VerifyPartManifests.py", 14)
    assert Report["counts"] == {"P01": 6, "P03": 8}
    assert Report["missing_target_refusals"] == 42
    assert (
        Report["replay_sha256"]
        == "c01ca63bd2fc5c306aaf072423da0aeb0c4209fdd2636abf19603e3a02399b27"
    )
