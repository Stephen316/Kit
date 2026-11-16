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
    PreviewDigests = Report["preview_sha256"]
    assert isinstance(PreviewDigests, dict)
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
