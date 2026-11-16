# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

"""Read, construct and independently compare the sealed two-pad mass cache."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from math import isclose
from pathlib import Path
from struct import calcsize, unpack
import sys

# resolve the existing research lane and its native evidence verifier consistently
ROOT = Path(__file__).resolve().parents[4]
sys.path[:0] = [
    str(ROOT / "src"),
    str(ROOT / "re/automation"),
    str(ROOT / "re/automation/TwoPad"),
    str(ROOT / "re/solidworks/WriterResearch"),
]

from CmgrBaseHeader import ReadCmgrHeader
from CmgrBossMass import BossMass, BossMassFields, Point, ReadBossMass
from CmgrCollectionFront import ReadCmgrFront
from CmgrColorReadback import ReadColorSpan
from CmgrInherited import ReadCmgrFeature
from CmgrMass import KGeometryLayout
from CmgrTwoPadMass import CalcTwoPadMass, EncodeTwoPadMass, PadBounds
from HeaderLogs import ReadHeaderLogs
from PadReceipts import ReadPadBytes
from PairedCaptureIntake import require
from PilotEvidence import pinned_record
from RectanglePairSketch import world
from VerifyCmgrBoss import GEOMETRY_TOLERANCES
from VerifyConfigMat import inspect_material
from VerifyDiscovery import AuditDiscovery
from convert.adapters.solidworks.Config.RootLayout import LoadPartLayouts
from convert.adapters.solidworks.Container.Archive import ArchiveError
from convert.adapters.solidworks.Container.ArchiveCursor import FieldCursor
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.api.ApiOpen import OpenDocument
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeEnd, ExtrudeFeature
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.GeometryCurves import LineGeometry

# the three source receipts bind the five positive pads and their healthy controls
CAPTURE_SOURCE = "463a3de14e4cb34aeeaa6aed1aa1e8b2804572c8"
NATIVE_REPORT = "bf0d74c06878c6c5063e4b9a55c61c2ef258bdc24323adbfb8f8d069bc77697e"
AUTHORING = "7c25ed3111ec45d9646e7b5de9df16f90f57528d3f2b97fc4e14f2666a2a884f"
REOPEN = "1ebdcdc23d4d220d549573dfb2c0cb45b1697ec7e42c192a3fb95bd34ba5699b"

# these represent the exact witnessed ordinary configuration profile
GENERATION = 19000
BODY_COUNT = 1
CAPTURE_DENSITY_KG_M3 = 1000.0


# exact saved sketch ownership supplies bounds before any mass field is read
def BoundsOf(Document: CadDocument, Step: FeatureStep) -> PadBounds:
    Definition = Step.definition
    if (
        not isinstance(Definition, ExtrudeFeature)
        or Definition.length is None
        or Definition.end_condition != ExtrudeEnd.KBlind
        or Definition.length.unit != "mm"
        or not isinstance(Definition.length.value, (int, float))
        or Definition.length.value <= 0
        or Definition.reversed
        or Definition.symmetric
    ):
        raise ArchiveError("two-pad mass requires owned positive blind depth")
    (Sketch,) = (Value for Value in Document.sketches if Value.id == Step.sketch_id)
    (Plane,) = (
        Value
        for Value in Document.support_planes
        if Value.id == Sketch.support_plane_id
    )
    (Loop,) = Sketch.closed_profile_entity_ids
    require(len(Loop) == len(set(Loop)) == 4, "four distinct owned perimeter sides")
    Entities = {Entity.id: Entity for Entity in Sketch.entities}
    Points: set[Point] = set()
    for Identity in Loop:
        Entity = Entities[Identity]
        Line = Entity.geometry
        if not isinstance(Line, LineGeometry) or Entity.construction:
            raise ArchiveError("two-pad mass requires only rectangular perimeter lines")
        A, B = (
            world(Plane.transform, PointValue) for PointValue in (Line.start, Line.end)
        )
        require(
            sum(First != Last for First, Last in zip(A, B, strict=True)) == 1,
            "orthogonal perimeter side",
        )
        for X, Y, Z in (A, B):
            Points.add((X / 1000, Y / 1000, Z / 1000))
    require(len(Points) == 4, "four owned perimeter vertices")
    Xs, Ys, Zs = ({PointValue[Axis] for PointValue in Points} for Axis in range(3))
    require(tuple(map(len, (Xs, Ys, Zs))) == (2, 2, 1), "axis-aligned pad rectangle")
    (Z,) = Zs
    return PadBounds(
        (min(Xs), min(Ys), Z),
        (max(Xs), max(Ys), Z + Definition.length.value / 1000),
    )


# public strict geometry ties both world-aligned prisms to the single joined body
def ReadBounds(Data: bytes) -> tuple[PadBounds, PadBounds]:
    Document = OpenDocument(Data, SourceFormat="solidworks.sldprt", StrictMode=True)
    Lower, Upper = (
        Step for Step in Document.feature_timeline if Step.operation is not None
    )
    (Solid,) = Document.bodies
    require(
        Lower.operation == Upper.operation == BooleanOp.KJoin
        and Solid.final_feature_id == Upper.id,
        "two positive pad owners contribute the single final solid",
    )
    return BoundsOf(Document, Lower), BoundsOf(Document, Upper)


# the record cursor must reach the same manager owner and saved stamps before mass
def ReadOwnedMass(Archive: SldprtArchive) -> tuple[BossMass, int, bytes]:
    Data = Archive.require("Contents/CMgr")
    _, _, Cursor = ReadColorSpan(Data, GENERATION)
    ReadCmgrFeature(Cursor, GENERATION)
    Manager = ReadCmgrHeader(Cursor, GENERATION)
    _, Session, Body = unpack("<3I", Archive.require("ModelStamps"))
    _, Header = ReadHeaderLogs(
        Archive.require("Contents/Config-0-ModelHeader"), GENERATION
    )
    require(
        (Manager.model_highest_id, Manager.session_stamp, Manager.mass_stamp)
        == (Header.NextTreeId - 1, Session, Body)
        and Header.UpdateStamp == Session,
        "same resolved model header and CMgr mass owner",
    )
    Start = Cursor.Offset
    Value = ReadBossMass(Cursor, GENERATION, BODY_COUNT)
    Saved = Data[Start : Cursor.Offset]
    ReadCmgrFront(Cursor, GENERATION, BodyCount=BODY_COUNT, SaveMode=1)
    return Value, Start, Saved


# compare geometry numerically and read every new record through the unchanged decoder
def CheckCase(Directory: Path, Capture: dict) -> dict[str, object]:
    Save = Capture["save"]
    Data = ReadPadBytes(Directory, Save["file"], Save["sha256"])
    Archive = SldprtArchive.from_bytes(Data)
    _, _, _, _, Density = inspect_material(
        Archive.require("Contents/Config-0"),
        GENERATION,
        LoadPartLayouts(),
        CAPTURE_DENSITY_KG_M3,
        False,
    )
    Lower, Upper = ReadBounds(Data)
    Saved, Start, Original = ReadOwnedMass(Archive)
    Calculated = CalcTwoPadMass(Lower, Upper, Density)
    Fresh = EncodeTwoPadMass(GENERATION, BODY_COUNT, Lower, Upper, Density)
    Cursor = FieldCursor(Fresh, 0)
    FreshValue = ReadBossMass(Cursor, GENERATION, BODY_COUNT)
    require(
        FreshValue == Calculated and Cursor.Offset == len(Fresh) == len(Original),
        "independent typed readback of the fresh complete mass record",
    )
    Wrapper = calcsize(KGeometryLayout)
    require(
        Fresh[Wrapper:] == Original[Wrapper:],
        "all existing default options and world frame match exactly",
    )
    Deltas = tuple(
        abs(A - B)
        for A, B in zip(BossMassFields(Saved), BossMassFields(FreshValue), strict=True)
    )
    require(
        all(A <= B for A, B in zip(Deltas, GEOMETRY_TOLERANCES, strict=True)),
        "all twelve physical cache fields match within existing tolerances",
    )
    return {
        "source_sha256": Save["sha256"],
        "density_kg_m3": Density,
        "record": [Start, Start + len(Fresh)],
        "centroid_z_displacement": 2 * calcsize("<d"),
        "saved_mass": BossMassFields(Saved),
        "generated_mass": BossMassFields(FreshValue),
        "absolute_deltas": Deltas,
        "wrapper_sha256": sha256(Fresh[Wrapper:]).hexdigest(),
        "source_record_sha256": sha256(Original).hexdigest(),
        "fresh_record_sha256": sha256(Fresh).hexdigest(),
    }


# malformed placement and wrapper controls exercise failure without custodial changes
def CheckRefusals() -> int:
    Base = PadBounds((0.0, 0.0, 0.0), (0.036, 0.024, 0.009))
    Top = PadBounds((0.012, 0.007, 0.009), (0.024, 0.017, 0.014))
    Density = 2875.0
    Good = EncodeTwoPadMass(GENERATION, BODY_COUNT, Base, Top, Density)
    Cursor = FieldCursor(Good, 0)
    Observed = ReadBossMass(Cursor, GENERATION, BODY_COUNT)
    require(
        Observed == CalcTwoPadMass(Base, Top, Density)
        and Cursor.Offset == len(Good)
        and isclose(Observed.MassKg, Density * Observed.VolumeM3, rel_tol=1e-15),
        "fresh distinguishable prisms and density round trip",
    )
    BadTop = (
        PadBounds((0.012, 0.007, 0.010), Top.Maximum),
        PadBounds((0.012, 0.007, 0.008), Top.Maximum),
        PadBounds((0.013, 0.007, 0.009), (0.025, 0.017, 0.014)),
        PadBounds((0.0, 0.007, 0.009), (0.036, 0.017, 0.014)),
        PadBounds(Top.Minimum, (0.024, 0.017, 0.009)),
    )
    Arguments = [(GENERATION, BODY_COUNT, Base, Value, Density) for Value in BadTop]
    Arguments.extend(
        (
            (GENERATION, BODY_COUNT, Base, Top, 0.0),
            (GENERATION, BODY_COUNT, Base, Top, float("nan")),
            (18000, BODY_COUNT, Base, Top, Density),
            (GENERATION, 2, Base, Top, Density),
        )
    )
    for Args in Arguments:
        try:
            EncodeTwoPadMass(*Args)
        except ArchiveError:
            continue
        raise ValueError("two-pad constructor accepted a contradictory scope")
    Corrupt = bytearray(Good)
    Corrupt[calcsize(KGeometryLayout)] ^= 1
    try:
        ReadBossMass(FieldCursor(bytes(Corrupt), 0), GENERATION, BODY_COUNT)
    except ArchiveError:
        return len(Arguments) + 1
    raise ValueError("typed readback accepted an altered mass option")


# immutable native provenance stays separate from the generated cached fields
def Report(Directory: Path) -> dict[str, object]:
    Native = AuditDiscovery(
        Directory, ROOT, CAPTURE_SOURCE, NATIVE_REPORT, AUTHORING, REOPEN, True
    )
    ReportValue = pinned_record(Directory / "report.json", NATIVE_REPORT)
    Cases = {
        Capture["variant"]: CheckCase(Directory, Capture)
        for Capture in ReportValue["observations"]["cases"]
    }
    return {
        "native_report_sha256": NATIVE_REPORT,
        "native_capture_source_revision": CAPTURE_SOURCE,
        "native_observations": Native["verified_native_observations"],
        "negative_controls": CheckRefusals(),
        "cases": Cases,
        "replay_sha256": sha256(
            json.dumps(
                Cases, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest(),
    }


if __name__ == "__main__":
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument("--run-directory", required=True, type=Path)
    print(
        json.dumps(
            Report(Parser.parse_args().run_directory), sort_keys=True, allow_nan=False
        )
    )
