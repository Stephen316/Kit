from hashlib import sha256 as DigestBytes
from json import loads as ParseJson
from math import isclose as CloseValue
from os import environ as ProcessEnv, pathsep as PathSep
from pathlib import Path as FilePath
from subprocess import CompletedProcess, run as RunProcess
from sys import executable as PythonExe
from typing import cast as CastValue

# the real command must use the same checkout as its committed authoring and independent evidence readers
KRepoRoot = FilePath(__file__).resolve().parents[3]

# measured discovery variations independently change each positive xy prism dimension
KDimensions = {
    "baseline-a": (40, 20, 10),
    "edit-width_mm-41": (41, 20, 10),
    "edit-height_mm-23": (40, 23, 10),
    "edit-depth_mm-12": (40, 20, 12),
}


# standalone authoring crosses allocation geometry material packing and saved record validation boundaries
def RunProbe(ScriptName: str, OutputPath: FilePath) -> CompletedProcess[str]:
    return RunProcess(
        [
            PythonExe,
            "-B",
            str(KRepoRoot / "re/Fusion/Reconstruction/DimensionAuthoring" / ScriptName),
            "--output",
            str(OutputPath),
        ],
        cwd=KRepoRoot,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=300,
        env={
            **ProcessEnv,
            "PYTHONPATH": PathSep.join(
                (str(KRepoRoot / "src"), str(KRepoRoot / "re/automation"))
            ),
        },
    )


# emitted literal dimensions must retain four unique parameters with separate sketch and boss owners
def VerifyDrivers(Candidate: dict[str, object], Sizes: tuple[int, int, int]) -> None:
    Parameters = CastValue(
        dict[str, dict[str, object]], Candidate["target_parameter_inventory"]
    )
    assert set(Parameters) == {"width_mm", "height_mm", "depth_mm", "d4"}
    Names = ("width_mm", "height_mm", "depth_mm", "d4")
    assert [Parameters[Driver]["slot"] for Driver in Names] == [1, 2, 3, 4]
    assert len({Parameters[Driver]["parameter_id"] for Driver in Names}) == 4
    assert len({Parameters[Driver]["binding_id"] for Driver in Names}) == 4
    assert Parameters["width_mm"]["owner_id"] == Parameters["height_mm"]["owner_id"]
    assert Parameters["depth_mm"]["owner_id"] == Parameters["d4"]["owner_id"]
    assert Parameters["width_mm"]["owner_id"] != Parameters["depth_mm"]["owner_id"]
    for Driver, Amount in zip(Names[:3], Sizes, strict=True):
        assert Parameters[Driver]["unit"] == "mm"
        assert Parameters[Driver]["value_native"] == Amount / 10.0
        assert Parameters[Driver]["expression"] == f"{Amount:g} mm"
    assert Parameters["d4"]["unit"] == "deg"
    assert Parameters["d4"]["value_native"] == 0.0
    assert Parameters["d4"]["expression"] == "0.0 deg"


# the real source derived command must publish only independently checked positive xy discovery candidates
def CheckDirectBoss(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Candidates"
    Process = RunProbe("SourceBossProbe.py", OutputPath)
    assert Process.returncode == 0, Process.stderr
    Payload = (OutputPath / "P03CandidateEvidence.json").read_bytes()
    assert Process.stdout.strip() == DigestBytes(Payload).hexdigest()
    Report = CastValue(dict[str, object], ParseJson(Payload))
    assert Report["qualification"] == "candidate_requires_licensed_target_acceptance"
    Candidates = CastValue(list[dict[str, object]], Report["candidates"])
    assert [Candidate["variant"] for Candidate in Candidates] == list(KDimensions)
    for Candidate in Candidates:
        Sizes = KDimensions[CastValue(str, Candidate["variant"])]
        VerifyDrivers(Candidate, Sizes)
        Content = (OutputPath / CastValue(str, Candidate["file"])).read_bytes()
        assert DigestBytes(Content).hexdigest() == Candidate["archive_sha256"]
        assert len(Content) == Candidate["archive_bytes"]
        BodyProof = CastValue(dict[str, object], Candidate["target_body"])
        assert BodyProof["body_count"] == 1
        assert CloseValue(
            CastValue(float, BodyProof["volume_mm3"]),
            Sizes[0] * Sizes[1] * Sizes[2],
            rel_tol=0,
            abs_tol=1e-6,
        )
        assert BodyProof["operation"] == "new_body"
        assert BodyProof["extent"] == "one_sided_positive_blind_from_profile_plane"
        assert BodyProof["topology_faces_edges_vertices"] == [6, 12, 8]
        Anchor = CastValue(
            dict[str, dict[str, object]], Candidate["target_anchor_and_dimensions"]
        )["anchor"]
        assert (
            CastValue(dict[str, object], Anchor["corner"])["id"]
            != CastValue(dict[str, object], Anchor["origin"])["id"]
        )


# the historical origin command must retain its default sketch only output and pinned fourteen control comparisons
def CheckOriginPath(TmpPath: FilePath) -> None:
    OutputPath = TmpPath / "Origin"
    Process = RunProbe("ProbeOrigin.py", OutputPath)
    assert Process.returncode == 0, Process.stderr
    Payload = (OutputPath / "OriginCoincidenceEvidence.json").read_bytes()
    assert Process.stdout.strip() == DigestBytes(Payload).hexdigest()
    Report = CastValue(dict[str, object], ParseJson(Payload))
    assert Report["native_application_acceptance"] is False
    Generated = CastValue(dict[str, object], Report["generated"])
    assert Generated["body_count"] == 0 and Generated["line_count"] == 4
    assert len(CastValue(list[object], Generated["dimensions"])) == 2
    Receipts = CastValue(
        dict[str, dict[str, object]],
        CastValue(dict[str, object], Report["controls"])["receipts"],
    )
    assert sorted(
        len(CastValue(list[object], Receipt["files"])) for Receipt in Receipts.values()
    ) == [6, 8]
