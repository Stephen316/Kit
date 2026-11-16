# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from Records import canonical

# a fixed witness scope keeps discovery captures outside the acceptance contract
WitnessScope = "generated-solidworks-rectangular-boss"

# the ordered edit roster gives each driver its own restoration boundary
DriveAxes = ("width", "height", "depth")


# the verifier must refuse incomplete or contradictory records before reporting proof
def RequireProof(Condition, Reason):
    if not Condition:
        raise ValueError(Reason)


# exact keys keep separately scoped records from acquiring witness authority
def CheckFields(Record, Fields):
    RequireProof(
        isinstance(Record, dict) and set(Record) == set(Fields.split()),
        f"expected fields: {Fields}",
    )


# verified metadata must have only one interpretation for each field
def UniqueFields(Pairs):
    Record = dict(Pairs)
    RequireProof(len(Record) == len(Pairs), "duplicate JSON fields")
    return Record


# the verifier reads only retained files under the selected private directory
def LocalFile(FilePath):
    RequireProof(
        FilePath.is_file() and FilePath.absolute() == FilePath.resolve(strict=True),
        f"expected a direct regular file: {FilePath.name}",
    )
    return FilePath.open("rb")


# signed digest pins link captured receipts without trusting mutable filenames
def ReadPinned(FilePath, Expected):
    with LocalFile(FilePath) as SourceFile:
        RawBytes = SourceFile.read(1024 * 1024 + 1)
    RequireProof(
        len(RawBytes) <= 1024 * 1024
        and hashlib.sha256(RawBytes).hexdigest() == Expected,
        f"metadata pin differs: {FilePath.name}",
    )
    Record = json.loads(RawBytes, object_pairs_hook=UniqueFields)
    RequireProof(isinstance(Record, dict), "witness metadata must be an object")
    canonical(Record)
    return Record


# preserved archives remain independent of writable scratch copies and native saves
def CheckArchive(FilePath, Expected):
    Hasher = hashlib.sha256()
    TotalSize = 0
    with LocalFile(FilePath) as SourceFile:
        while Block := SourceFile.read(1024 * 1024):
            TotalSize += len(Block)
            RequireProof(TotalSize <= 256 * 1024 * 1024, "archive exceeds 256 MiB")
            Hasher.update(Block)
    RequireProof(
        TotalSize > 0 and Hasher.hexdigest() == Expected,
        f"archive pin differs: {FilePath.name}",
    )


# numeric comparisons must refuse flags and nonfinite values in native evidence
def ReadScalar(Value):
    RequireProof(
        type(Value) in (int, float) and math.isfinite(Value),
        "expected a finite numeric measurement",
    )
    return float(Value)


# three coordinates keep world placements and mass measurements comparable
def ReadPoint(Value):
    RequireProof(isinstance(Value, list) and len(Value) == 3, "expected a 3D point")
    return tuple(ReadScalar(Coord) for Coord in Value)


# linked measure checks allow native floating point noise at the observed scale
def CheckNear(Observed, Expected, Tolerance=1e-10):
    RequireProof(
        math.isclose(ReadScalar(Observed), Expected, rel_tol=0, abs_tol=Tolerance),
        "native measurement differs from the plan",
    )


# comparisons preserve world coordinate order through the candidate lifecycle
def CheckPoint(Observed, Expected):
    for Actual, Target in zip(ReadPoint(Observed), Expected, strict=True):
        CheckNear(Actual, Target)


# the generated profile and extrusion direction supply independent body expectations
def ShapeMeasures(Shape):
    CheckFields(Shape, "corners_m depth_m direction")
    Corners = Shape["corners_m"]
    RequireProof(
        isinstance(Corners, list) and len(Corners) == 4, "expected four corners"
    )
    First, Second, Third, Fourth = (ReadPoint(Point) for Point in Corners)
    Width = math.dist(First, Second)
    Height = math.dist(Second, Third)
    Depth = ReadScalar(Shape["depth_m"])
    Direction = ReadPoint(Shape["direction"])
    RequireProof(min(Width, Height, Depth) > 0, "expected a nondegenerate prism")
    WidthLine = tuple(
        (Right - Left) / Width for Left, Right in zip(First, Second, strict=True)
    )
    HeightLine = tuple(
        (Right - Left) / Height for Left, Right in zip(Second, Third, strict=True)
    )
    CheckNear(math.hypot(*Direction), 1, 1e-8)
    CheckNear(
        math.fsum(
            Axis * Other for Axis, Other in zip(WidthLine, HeightLine, strict=True)
        ),
        0,
        1e-8,
    )
    for Edge in (WidthLine, HeightLine):
        CheckNear(
            math.fsum(
                Axis * Other for Axis, Other in zip(Edge, Direction, strict=True)
            ),
            0,
            1e-8,
        )
    for Left, Right, Opposite, Last in zip(First, Second, Third, Fourth, strict=True):
        CheckNear(Last, Left + Opposite - Right)
    Center = tuple(
        math.fsum(Coordinates) / 4 + Depth * Axis / 2
        for Coordinates, Axis in zip(
            zip(First, Second, Third, Fourth, strict=True), Direction, strict=True
        )
    )
    return (Width, Height, Depth), Width * Height * Depth, Center


# each edit must isolate one of the three known independent dimension owners
def CheckEditPlan(Shapes):
    CheckFields(Shapes, "baseline width height depth")
    BaseDims, _, _ = ShapeMeasures(Shapes["baseline"])
    for Index, Axis in enumerate(DriveAxes):
        Dimensions, _, _ = ShapeMeasures(Shapes[Axis])
        CheckPoint(Shapes[Axis]["direction"], Shapes["baseline"]["direction"])
        for Slot, (Proposed, Original) in enumerate(
            zip(Dimensions, BaseDims, strict=True)
        ):
            if Slot == Index:
                RequireProof(
                    abs(Proposed - Original) > 2e-10, "edit has no measurable effect"
                )
            else:
                CheckNear(Proposed, Original)


# generation output must bind the same archive and independent baseline geometry
def CheckGeneration(Report, Plan):
    RequireProof(
        Report["archive_sha256"] == Plan["candidate_sha256"],
        "generation report names a different candidate archive",
    )
    Baseline = Plan["shapes"]["baseline"]
    Measures, Volume, Center = ShapeMeasures(Baseline)
    Width, Height, SignedDepth = ReadPoint(Report["dimensions_mm"])
    CheckPoint([Width / 1000, Height / 1000, abs(SignedDepth) / 1000], Measures)
    CheckNear(Report["volume_m3"], Volume, 1e-14)
    CheckPoint(Report["centroid_metres"], Center)
    Corners = list(map(ReadPoint, Baseline["corners_m"]))
    Normal = ReadPoint(Baseline["direction"])
    First, Second, Third, _ = Corners
    Across = tuple(Right - Left for Left, Right in zip(First, Second, strict=True))
    Along = tuple(Right - Left for Left, Right in zip(Second, Third, strict=True))
    Winding = math.fsum(
        Normal[Index]
        * (
            Across[(Index + 1) % 3] * Along[(Index + 2) % 3]
            - Across[(Index + 2) % 3] * Along[(Index + 1) % 3]
        )
        for Index in range(3)
    )
    RequireProof(SignedDepth * Winding > 0, "generated depth direction differs")
    for Point in Corners[:]:
        Corners.append(
            tuple(
                Value + Axis * Measures[2]
                for Value, Axis in zip(Point, Normal, strict=True)
            )
        )
    Coordinates = tuple(zip(*Corners, strict=True))
    Bounds = Report["bounds_metres"]
    RequireProof(
        isinstance(Bounds, list) and len(Bounds) == 2, "expected generated world bounds"
    )
    for Bound, Target in zip(
        Bounds,
        (tuple(map(min, Coordinates)), tuple(map(max, Coordinates))),
        strict=True,
    ):
        CheckPoint(Bound, Target)


# an exact plan pins the independently generated candidate and stock control
def VerifyPlan(RootPath, PlanHash):
    Plan = ReadPinned(RootPath / "Plan.json", PlanHash)
    CheckFields(
        Plan,
        "schema scope source_revision build image_sha256 candidate_sha256 "
        "generation_sha256 control history drivers shapes",
    )
    RequireProof(
        type(Plan["schema"]) is int
        and Plan["schema"] == 1
        and Plan["scope"] == WitnessScope,
        "unexpected witness plan",
    )
    RequireProof(
        re.fullmatch(r"[0-9a-f]{40}", Plan["source_revision"]),
        "expected the fixture source revision",
    )
    RequireProof(
        re.fullmatch(r"[0-9]+(?:\.[0-9]+){3}", Plan["build"]),
        "expected an exact SOLIDWORKS build",
    )
    RequireProof(
        re.fullmatch(r"[0-9a-f]{64}", Plan["image_sha256"]),
        "expected an installed image pin",
    )
    History = Plan["history"]
    Drivers = Plan["drivers"]
    RequireProof(
        isinstance(History, list)
        and len(History) == 2
        and isinstance(Drivers, list)
        and len(Drivers) == 3
        and all(
            isinstance(Label, str) and 0 < len(Label) <= 128
            for Label in History + Drivers
        )
        and len(set(History + Drivers)) == 5,
        "expected distinct sketch boss and driver names",
    )
    Control = Plan["control"]
    CheckFields(Control, "sha256 volume_m3 centroid_m")
    RequireProof(ReadScalar(Control["volume_m3"]) > 0, "expected a solid stock control")
    ReadPoint(Control["centroid_m"])
    RequireProof(
        Control["sha256"] != Plan["candidate_sha256"],
        "control and candidate must be independent",
    )
    CheckEditPlan(Plan["shapes"])
    Generation = ReadPinned(RootPath / "Generation.json", Plan["generation_sha256"])
    CheckGeneration(Generation, Plan)
    CheckArchive(RootPath / "Candidate.SLDPRT", Plan["candidate_sha256"])
    CheckArchive(RootPath / "Control.SLDPRT", Control["sha256"])
    return Plan


# native operation return values must rule out a nominally successful warning
def CheckOperation(Operation):
    CheckFields(Operation, "returned errors warnings")
    RequireProof(
        Operation["returned"] is True
        and all(
            type(Operation[Key]) is int and Operation[Key] == 0
            for Key in ("errors", "warnings")
        ),
        "native open or save did not return cleanly",
    )


# both sides of each application phase need the same measured stock model
def CheckControl(Observed, Expected):
    CheckFields(Observed, "sha256 open rebuild body_count volume_m3 centroid_m")
    CheckOperation(Observed["open"])
    RequireProof(
        Observed["sha256"] == Expected["sha256"]
        and Observed["rebuild"] is True
        and type(Observed["body_count"]) is int
        and Observed["body_count"] == 1,
        "healthy control did not reopen and rebuild its expected solid",
    )
    CheckNear(Observed["volume_m3"], Expected["volume_m3"], 1e-14)
    CheckPoint(Observed["centroid_m"], Expected["centroid_m"])


# a complete process receipt distinguishes normal exit from forced native recovery
def CheckProcess(Phase, Plan):
    Owner = Phase["owner"]
    Exited = Phase["exit"]
    CheckFields(Owner, "pid created session image_sha256 initial_documents verified")
    CheckFields(Exited, "pid created finished exit_code drained")
    for Entry in (Owner, Exited):
        RequireProof(
            type(Entry["pid"]) is int
            and 0 < Entry["pid"] <= 0xFFFFFFFF
            and type(Entry["created"]) is int
            and 0 < Entry["created"] < 1 << 64,
            "expected exact windows process identity",
        )
    RequireProof(
        Owner["pid"] == Exited["pid"]
        and Owner["created"] == Exited["created"]
        and Owner["image_sha256"] == Plan["image_sha256"]
        and Owner["verified"] is True
        and type(Owner["session"]) is int
        and Owner["session"] > 0
        and type(Owner["initial_documents"]) is int
        and Owner["initial_documents"] == 0
        and type(Exited["finished"]) is int
        and Owner["created"] < Exited["finished"] < 1 << 64
        and type(Exited["exit_code"]) is int
        and Exited["exit_code"] == 0
        and Exited["drained"] is True,
        "owned process identity or normal exit is unproven",
    )


# native drivers must stay attached to the planned sketch and extrusion owners
def CheckDrivers(Observed, Plan, Dimensions):
    RequireProof(
        isinstance(Observed, list) and len(Observed) == 3,
        "expected three owned drivers",
    )
    Sketch, Boss = Plan["history"]
    for Driver, Axis, Name, Owner, Size in zip(
        Observed,
        DriveAxes,
        Plan["drivers"],
        (Sketch, Sketch, Boss),
        Dimensions,
        strict=True,
    ):
        CheckFields(Driver, "axis name owner driving value_m")
        RequireProof(
            Driver["axis"] == Axis
            and Driver["name"] == Name
            and Driver["owner"] == Owner
            and Driver["driving"] is True,
            "native driver lost its expected feature owner",
        )
        CheckNear(Driver["value_m"], Size)


# edit reports need nonprovisional geometry and mass measurements at every stage
def CheckMeasure(Observed, Stage, Shape, Plan):
    CheckFields(
        Observed,
        "stage history boss_profile blind fully_constrained rebuilt body_count "
        "corners_m direction depth_m drivers volume_m3 centroid_m",
    )
    Dimensions, Volume, Center = ShapeMeasures(Shape)
    RequireProof(
        Observed["stage"] == Stage
        and Observed["history"] == Plan["history"]
        and Observed["boss_profile"] == Plan["history"][0]
        and Observed["blind"] is True
        and Observed["fully_constrained"] is True
        and Observed["rebuilt"] is (Stage != "before_rebuild")
        and type(Observed["body_count"]) is int
        and Observed["body_count"] == 1,
        f"incomplete native history or rebuild at {Stage}",
    )
    RequireProof(
        isinstance(Observed["corners_m"], list) and len(Observed["corners_m"]) == 4,
        "expected four native corners",
    )
    for Point, Target in zip(Observed["corners_m"], Shape["corners_m"], strict=True):
        CheckPoint(Point, Target)
    CheckPoint(Observed["direction"], Shape["direction"])
    CheckNear(Observed["depth_m"], Dimensions[2])
    CheckDrivers(Observed["drivers"], Plan, Dimensions)
    RequireProof(ReadScalar(Observed["volume_m3"]) > 0, "solid volume must be positive")
    CheckNear(Observed["volume_m3"], Volume, 1e-14)
    CheckPoint(Observed["centroid_m"], Center)


# fixed phase roles stop read only diagnostics from standing in for writable observations
def ReadPhase(RootPath, PhaseName, Expected, Plan, PlanHash):
    Phase = ReadPinned(RootPath / f"{PhaseName.title()}.json", Expected)
    CheckFields(
        Phase,
        "schema scope phase status plan_sha256 prior_sha256 build owner exit "
        "input_sha256 output_sha256 read_only open controls measurements save",
    )
    RequireProof(
        type(Phase["schema"]) is int
        and Phase["schema"] == 1
        and Phase["scope"] == WitnessScope
        and Phase["phase"] == PhaseName
        and Phase["status"] == "observed"
        and Phase["plan_sha256"] == PlanHash
        and Phase["build"] == Plan["build"]
        and Phase["read_only"] is (PhaseName == "reopen"),
        "native phase does not bind the exact plan and phase mode",
    )
    CheckOperation(Phase["open"])
    CheckProcess(Phase, Plan)
    CheckFields(Phase["controls"], "before after")
    for Control in Phase["controls"].values():
        CheckControl(Control, Plan["control"])
    return Phase


# the fixed chronology binds every independent restoration to the saved baseline
def CheckLifecycle(Edit, Reopen, EditHash, Plan):
    Saved = Edit["output_sha256"]
    RequireProof(
        Edit["prior_sha256"] is None
        and Edit["input_sha256"] == Plan["candidate_sha256"]
        and Reopen["prior_sha256"] == EditHash
        and Reopen["input_sha256"] == Saved
        and Reopen["output_sha256"] == Saved
        and Reopen["save"] is None,
        "restored archive is not the exact fresh reopen input",
    )
    RequireProof(
        Edit["exit"]["finished"] < Reopen["owner"]["created"]
        and Edit["owner"]["session"] == Reopen["owner"]["session"],
        "reopen did not start after the original owned process drained",
    )
    CheckOperation(Edit["save"])
    Shapes = Plan["shapes"]
    Baseline = Shapes["baseline"]
    EditStages = [("baseline", Baseline)]
    for Axis in DriveAxes:
        EditStages.extend(
            ((f"{Axis}_edited", Shapes[Axis]), (f"{Axis}_restored", Baseline))
        )
    for Phase, Stages in (
        (Edit, EditStages),
        (Reopen, (("before_rebuild", Baseline), ("after_rebuild", Baseline))),
    ):
        Observations = Phase["measurements"]
        RequireProof(
            isinstance(Observations, list) and len(Observations) == len(Stages),
            "native measurement sequence is incomplete",
        )
        for Observed, (Stage, Shape) in zip(Observations, Stages, strict=True):
            CheckMeasure(Observed, Stage, Shape, Plan)
    return Saved


# an offline run can check a handoff plan before any licensed process is available
def VerifyWitness(RootPath, PlanHash, EditHash, ReopenHash):
    Plan = VerifyPlan(RootPath, PlanHash)
    Report = {
        "scope": WitnessScope,
        "status": "verified_witness_plan",
        "plan_sha256": PlanHash,
        "source_revision": Plan["source_revision"],
        "candidate_sha256": Plan["candidate_sha256"],
        "native_observations_verified": False,
    }
    RequireProof(
        (EditHash is None) == (ReopenHash is None), "provide both native phase pins"
    )
    if EditHash is None:
        return Report
    Edit = ReadPhase(RootPath, "edit", EditHash, Plan, PlanHash)
    Reopen = ReadPhase(RootPath, "reopen", ReopenHash, Plan, PlanHash)
    Saved = CheckLifecycle(Edit, Reopen, EditHash, Plan)
    CheckArchive(RootPath / "Restored.SLDPRT", Saved)
    return {
        **Report,
        "status": "verified_native_witness",
        "native_observations_verified": True,
        "build": Plan["build"],
        "edit_sha256": EditHash,
        "reopen_sha256": ReopenHash,
        "restored_sha256": Saved,
    }


# the command performs no application dispatch or repository state updates
def MainRun():
    Parser = argparse.ArgumentParser(
        description="Verify a retained SOLIDWORKS rectangular Boss witness"
    )
    Parser.add_argument("--witness", type=Path, required=True)
    Parser.add_argument("--plan-sha256", required=True)
    Parser.add_argument("--edit-sha256")
    Parser.add_argument("--reopen-sha256")
    Args = Parser.parse_args()
    try:
        Result = VerifyWitness(
            Args.witness, Args.plan_sha256, Args.edit_sha256, Args.reopen_sha256
        )
    except (OSError, ValueError, TypeError, KeyError, OverflowError) as Error:
        Parser.exit(1, f"witness refused: {Error}\n")
    print(canonical(Result))
    return 0


if __name__ == "__main__":
    raise SystemExit(MainRun())
