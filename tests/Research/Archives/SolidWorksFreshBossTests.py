from hashlib import sha256 as DigestBytes
from json import dumps as EncodeJson, loads as ParseJson
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe
from tempfile import TemporaryDirectory as MakeFolder
from typing import cast as CastValue
from uuid import UUID as OwnedUuid

from pytest import approx as Approx

# independent synthetic identities keep the authored archive stable across hosted runs
KFixtureIds = tuple(str(OwnedUuid(int=Index, version=4)) for Index in range(1, 11))

# database creation uses its own local wall clock in the ordinary package format
KExchangeTime = "2026-07-09T12:30:28"

# explicit colors keep the witness preview reproducible from the authored geometry
KPreviewColors = ((246, 247, 249), (20, 32, 40), (148, 171, 188))

# independently supplied density must reach both material records and the mass
KPortDensity = 1850.0

# the fixture explicitly selects the measured ordinary header classification
KFixtureLicense = {
    "package_code": 4,
    "license_type": 2,
    "visible_sketches": True,
    "terminal_flag": 1,
}

# the source free case declares every save and appearance input away from the writer
KFreshContext = {
    "saved_path": r"C:\KitFixture\FreshBoss.SLDPRT",
    "created_utc": "2026-07-09T12:30:26+00:00",
    "appearance_asset": r"C:\KitFixture\data\graphics\materials\color.p2m",
    "preview_colors": KPreviewColors,
    "block_id": KFixtureIds[0],
    "calendar": {"date": "2026-07-09", "utc_offset_minutes": 0},
    "license": KFixtureLicense,
    "definition": {
        "camera": [0.0, 0.0, 0.0, 1.0],
        "journal": {"name": "", "time": 0, "state": 0},
        "terminal_value": 0.0,
    },
    "config_exchange": {"id": KFixtureIds[1], "created": KExchangeTime},
    "object_exchange": {
        "folder": KFixtureIds[2],
        "planes": KFixtureIds[3:6],
        "document": KFixtureIds[6],
        "created": KExchangeTime,
        "index_order": [2, 0, 1],
    },
    "pmi": {"keys": KFixtureIds[7:10], "created": KExchangeTime},
    "content": {
        "material_name": "Steel",
        "material_id": "fixture-steel",
        "body_visible": True,
    },
}


# the native candidate command receives the same explicit fixture context on each invocation
def RunFreshBoss(Destination: FilePath) -> CompletedProcess[str]:
    RootPath = FilePath(__file__).resolve().parents[3]
    ProgramPath = RootPath / "re/solidworks/WriterResearch/VerifyFreshBoss.py"
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(ProgramPath),
            "--fixture-context",
            "-",
            "--candidate",
            str(Destination),
        ],
        cwd=RootPath,
        input=EncodeJson(KFreshContext),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )


# the exported bytes must bind the in memory readback and preserve any competing destination
def LoadCandidate(Destination: FilePath) -> dict[str, object]:
    Result = RunFreshBoss(Destination)
    assert Result.returncode == 0, Result.stderr
    Report: dict[str, object] = ParseJson(Result.stdout)
    assert DigestBytes(Destination.read_bytes()).hexdigest() == Report["archive_sha256"]
    Existing = b"independent existing candidate"
    assert Destination.write_bytes(Existing) == len(Existing)
    Retry = RunFreshBoss(Destination)
    assert Retry.returncode != 0, Retry.stdout
    assert "already exists" in Retry.stderr
    assert Destination.read_bytes() == Existing
    return Report


# the hosted process must reopen the independently authored part and preserve its driving graph
def CheckFreshBoss() -> None:
    with MakeFolder() as TempRoot:
        Report = LoadCandidate(FilePath(TempRoot) / "FreshBoss.SLDPRT")
    Bounds = CastValue(list[list[float]], Report["bounds_metres"])
    assert Report["stream_count"] == 32
    PreviewValue = Report["preview_sha256"]
    assert isinstance(PreviewValue, dict)
    PreviewDigests = CastValue(dict[str, object], PreviewValue)
    assert set(PreviewDigests) == {"Preview", "PreviewPNG"}
    assert all(
        isinstance(Value, str) and len(Value) == 64 for Value in PreviewDigests.values()
    )
    assert Report["feature_ids"] == [26, 34]
    assert Report["dimension_ids"] == [72, 73, 74]
    assert Report["dimensions_mm"] == Approx([38.25, 22.5, -7.75])
    assert Bounds[0] == Approx([0.0, 0.0, -0.00775])
    assert Bounds[1] == Approx([0.03825, 0.0225, 0.0])
    assert Report["volume_m3"] == Approx(0.00000666984375)
    assert Report["centroid_metres"] == Approx([0.019125, 0.01125, -0.003875])


# the child process loads the typed research interface from this exact checkout
KPortImports = """
import json
import sys
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "re/solidworks/WriterResearch"))
from VerifyFreshBoss import (
    ArchiveFeature, AuthoredTimes, BossIds, ConfigClocks, FileClock,
    FixtureCfgPrefs, KMemberIds, KPartGeneration, MetadataContext, MetadataTimes,
    PackageIdentity, ParseContext, PortableBossContext, SystemClocks,
    VerifyPortableBoss, authored_case, wire_state,
)
from interchange.document.Models.DocumentModel import CadDocument
"""

# the caller supplies independent neutral dimensions and chooses its own saved view centre
KPortGraph = """
case, raw_package = json.load(sys.stdin)
package: dict[str, object] = raw_package
reference = ParseContext(json.dumps(package))
document = authored_case(case["right"], *case["dimensions_mm"])
sketch, = document.sketches
body, = document.bodies
plane, = document.support_planes
datum_name = "Right Plane" if case["right"] else "Front Plane"
document = replace(
    document,
    support_planes=(replace(plane, name=datum_name),),
    bodies=(replace(body, name=document.feature_timeline[1].name),),
)
first, second, third = reference.Definition.Views
density = case["density_kg_m3"]
terminal_density = density + 1 if case.get("reject") == "definition density" else density
definition = replace(
    reference.Definition,
    Views=(replace(first, centre=tuple(case["centre_m"])), second, third),
    TerminalValue=terminal_density,
)
"""

# native feature and presentation inputs belong to the test caller
KPortWires = """
created = int(reference.Created.timestamp())
shared = FileClock(reference.Created)
profile_time = FileClock(reference.Created + timedelta(seconds=1))
boss_time = FileClock(reference.Created + timedelta(seconds=2))
title = case["title"]
_, profile, boss = wire_state()
trim_file = replace(profile.Trim.File, Title=title, SavedTime=created)
if case.get("reject") == "trim path":
    trim_file = replace(trim_file, FilePath="C:/Other/Unrelated.SLDPRT", Flags=8)
profile = replace(
    profile,
    Feature=replace(profile.Feature, FileTime=profile_time),
    DatumTime=created, OriginTime=created,
    Trim=replace(profile.Trim, File=trim_file, ReferenceTime=created + 1),
)
boss = replace(
    boss, Feature=replace(boss.Feature, FileTime=boss_time), ReferenceTime=created + 2,
)
prefs = FixtureCfgPrefs(case.get("units", "metric"))
prefs = replace(
    prefs, Title=title, BlockIdentity=reference.BlockId, DensityKgM3=density,
    Visual=replace(prefs.Visual, NativeAssetPath=reference.AssetPath, AppearanceId=121),
)
identities = PackageIdentity(
    SavedPath=reference.SavedPath, Calendar=reference.Calendar,
    Exchange=reference.Exchange, Objects=reference.Objects, Pmi=reference.Pmi,
    Content=reference.Content, PreviewColors=reference.PreviewColors,
)
"""

# the whole package consumes caller chosen ids and distinct typed lifecycle owners
KPortContext = """
context = PortableBossContext(
    Ids=BossIds(**dict(zip(("Profile", "Operation", "Width", "Height", "Depth"), case["ids"], strict=True))),
    Profile=profile, Boss=boss, Preferences=prefs,
    ConfigTime=ConfigClocks(
        GeometryStamp=251, DocumentUpdateStamp=267, BodyStamp=281,
        SketchBlock=shared, ExplodedView=shared,
    ),
    SystemTime=SystemClocks(
        Members={
            identity: ArchiveFeature(201 + identity, KPartGeneration, 2026225, shared)
            for identity in KMemberIds
        },
        FrontTime=created, RightTime=created, OriginTime=created, OriginState=103,
    ),
    Metadata=MetadataContext(
        UserName="Portable caller", HistoryName=title, NextTreeId=90,
        Times=MetadataTimes(
            HistoryStart=created, Created=created, SummaryCreated=created,
            Modified=created + 4, Updated=created + 3,
            Profile=AuthoredTimes(Created=created + 1, Rebuilt=created + 2),
            Boss=AuthoredTimes(Created=created + 2, Rebuilt=created + 3),
        ),
        Header=reference.Header, Definition=definition, ManagerTime=shared, PartTime=shared,
    ),
    Package=identities,
)
"""

# rejected requests exercise the same neutral parsing and archive boundary as accepted ones
KPortRefusals = """
rejection = case.get("reject")
if rejection == "body":
    document = replace(document, bodies=(replace(body, name="Independent body label"),))
elif rejection == "metadata":
    document = replace(document, metadata={"unknown_semantics": True})
elif rejection == "nested":
    parameter, *others = document.parameters
    document = replace(
        document, parameters=(replace(parameter, attributes={"unmapped": True}), *others),
    )
elif rejection == "unframed":
    document = replace(
        document, sketches=(replace(sketch, attributes={"unframed_support_plane_native_id": 4}),),
    )
elif rejection == "datum clock":
    context = replace(context, Profile=replace(profile, DatumTime=created + 1))
elif rejection == "material":
    context = replace(
        context, Package=replace(identities, Content=replace(identities.Content, MaterialName="Steel")),
    )
"""


# direct construction bypasses json validation so the entry point must enforce it
KPortRun = """
document = CadDocument.from_json(document.to_json())
if rejection == "invalid graph":
    sketch, = document.sketches
    document = replace(document, sketches=(replace(sketch, support_plane_id="missing-plane"),))
result = VerifyPortableBoss(document, context, Candidate=Path(sys.argv[1]))
print(json.dumps(result))
"""


# each child receives the same checked research entry and its own independent inputs
KPortableCaller = (
    KPortImports + KPortGraph + KPortWires + KPortContext + KPortRefusals + KPortRun
)


# each front direction uses independently chosen neutral dimensions and target identities
KFrontCases: tuple[dict[str, object], ...] = (
    {
        "right": False,
        "title": "PortableFrontReverse",
        "first_key": 20,
        "dimensions_mm": [31.25, 19.5, -6.75],
        "ids": [53, 67, 81, 82, 83],
        "datum": 2,
        "bounds": [[0.0, 0.0, -0.00675], [0.03125, 0.0195, 0.0]],
        "centre_m": [0.015625, 0.00975, -0.003375],
    },
    {
        "right": False,
        "title": "PortableFrontForward",
        "first_key": 40,
        "dimensions_mm": [36.75, 16.25, 8.5],
        "ids": [55, 69, 87, 88, 89],
        "datum": 2,
        "bounds": [[0.0, 0.0, 0.0], [0.03675, 0.01625, 0.0085]],
        "centre_m": [0.018375, 0.008125, 0.00425],
    },
)


# each right direction must translate local sketch lengths into independently computed world bounds
KRightCases: tuple[dict[str, object], ...] = (
    {
        "right": True,
        "title": "PortableRightForward",
        "first_key": 30,
        "dimensions_mm": [45.5, 23.75, 12.25],
        "ids": [54, 68, 84, 85, 86],
        "datum": 4,
        "bounds": [[0.0, 0.0, 0.0], [0.01225, 0.0455, 0.02375]],
        "centre_m": [0.006125, 0.02275, 0.011875],
    },
    {
        "right": True,
        "title": "PortableRightReverse",
        "first_key": 50,
        "dimensions_mm": [40.25, 27.5, -15.5],
        "ids": [56, 70, 71, 76, 79],
        "datum": 4,
        "bounds": [[-0.0155, 0.0, 0.0], [0.0, 0.04025, 0.0275]],
        "centre_m": [-0.00775, 0.020125, 0.01375],
    },
)


# the test passes the targeted package identities independently of the requested neutral dimensions
def RunPortable(
    CaseValue: dict[str, object], Destination: FilePath
) -> CompletedProcess[str]:
    Title = CastValue(str, CaseValue["title"])
    FirstKey = CastValue(int, CaseValue["first_key"])
    KeyValues = tuple(
        str(OwnedUuid(int=Index, version=4)) for Index in range(FirstKey, FirstKey + 10)
    )
    Package = {
        **KFreshContext,
        "saved_path": f"C:\\KitFixture\\{Title}.SLDPRT",
        "block_id": KeyValues[0],
        "config_exchange": {"id": KeyValues[1], "created": KExchangeTime},
        "object_exchange": {
            "folder": KeyValues[2],
            "planes": KeyValues[3:6],
            "document": KeyValues[6],
            "created": KExchangeTime,
            "index_order": [1, 2, 0],
        },
        "pmi": {"keys": KeyValues[7:10], "created": KExchangeTime},
        "content": {
            "material_name": "Material <not specified>",
            "material_id": CaseValue.get("material_id", "Steel"),
            "body_visible": True,
        },
    }
    return RunProcess(
        [PythonExe, "-B", "-c", KPortableCaller, str(Destination)],
        cwd=FilePath(__file__).resolve().parents[3],
        input=EncodeJson(({**CaseValue, "density_kg_m3": KPortDensity}, Package)),
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )


# the whole archive must retain independently specified axes and editable sizes and owners
def CheckPortable() -> None:
    with MakeFolder() as TempRoot:
        for Ordinal, CaseValue in enumerate((*KFrontCases, *KRightCases)):
            Destination = FilePath(TempRoot) / f"Portable{Ordinal}.SLDPRT"
            Result = RunPortable(CaseValue, Destination)
            assert Result.returncode == 0, Result.stderr
            Report: dict[str, object] = ParseJson(Result.stdout)
            assert (
                DigestBytes(Destination.read_bytes()).hexdigest()
                == Report["archive_sha256"]
            )
            assert Report["stream_count"] == 32
            assert Report["centroid_metres"] == Approx(
                CastValue(list[float], CaseValue["centre_m"])
            )
            IdentityValues = CastValue(list[int], CaseValue["ids"])
            Readback = CastValue(dict[str, object], Report["readback"])
            assert Readback["feature_ids"] == IdentityValues[:2]
            assert Readback["dimension_ids"] == IdentityValues[2:]
            assert Readback["dimensions_mm"] == Approx(
                CastValue(list[float], CaseValue["dimensions_mm"])
            )
            Bounds = CastValue(list[list[float]], CaseValue["bounds"])
            ActualBounds = CastValue(list[list[float]], Readback["bounds_metres"])
            assert ActualBounds[0] == Approx(Bounds[0])
            assert ActualBounds[1] == Approx(Bounds[1])
            assert Readback["datum_id"] == CaseValue["datum"]
            assert Readback["origin_support_id"] == 2
            assert Readback["datum_time"] == Readback["origin_support_time"]
            assert Readback["density_kg_m3"] == KPortDensity


# a rejected portable input must leave the requested destination unused
def CheckPortReject() -> None:
    with MakeFolder() as TempRoot:
        Destination = FilePath(TempRoot) / "Refused.SLDPRT"
        for Reason, Message in (
            ("body", "preserve the authored names"),
            ("metadata", "unsupported document metadata"),
            ("nested", "unsupported nested attributes"),
            ("unframed", "unqualified SOLIDWORKS sketch support"),
            ("datum clock", "same datum and Origin times"),
            ("material", "unassigned compatibility material labels"),
            ("invalid graph", "sketch drawing references missing plane"),
            ("definition density", "Config and Definition density must agree"),
            ("trim path", "standalone contour requires an empty trim path"),
        ):
            Result = RunPortable({**KRightCases[0], "reject": Reason}, Destination)
            assert Result.returncode != 0, Result.stdout
            assert Message in Result.stderr
            assert not Destination.exists()
        Result = RunPortable({**KRightCases[0], "units": "inch"}, Destination)
        assert Result.returncode != 0, Result.stdout
        assert "witnessed metric display settings" in Result.stderr
        assert not Destination.exists()


# the correct name cannot make a foreign material key a supported compatibility value
def CheckPortMatKey() -> None:
    with MakeFolder() as TempRoot:
        Destination = FilePath(TempRoot) / "ForeignMaterial.SLDPRT"
        Result = RunPortable(
            {**KRightCases[0], "material_id": "unmapped-native-key"}, Destination
        )
        assert Result.returncode != 0, Result.stdout
        assert "unassigned compatibility material labels" in Result.stderr
        assert not Destination.exists()
