"""Report typed sketch geometry from the eleven pinned P04 discovery captures."""

from argparse import ArgumentParser
from collections import Counter
from hashlib import sha256 as Sha256
import json as Json
from math import hypot as Hypot
from pathlib import Path
import re as Regex
from subprocess import check_output as CheckOutput
from sys import path as ImportPaths
from sys import stdout as StandardOutput

# discovery claims must replay against the original immutable capture revision
KCaptureRev = "466dcb172dfa3803463e07ccde963ba01671d200"

# this folder isolates the qualified solidworks discovery evidence from other captures
KCaptureFolder = "re/automation/PairedCaptures/P04/solidworks-c1986308375a"

# the exact receipt binds all native saves and the independent measurement digest
KReceiptDigest = "7fd2fffa3c690998753a80cab81da2f1c2446c9fcec39574e3983a7f4345cae5"

# accepted display framing is scoped to the independently witnessed platform build
KApplicationBuild = "34.4.1.1011"


# git blob reads avoid workspace capture changes and never invoke licensed software
def ReadPinned(RootPath, FileName):
    ObjectPath = f"{KCaptureRev}:{KCaptureFolder}/{FileName}"
    return CheckOutput(["git", "show", ObjectPath], cwd=RootPath)


# saved geometry and measured geometry must come from the same verified capture set
def ReadReceipts(RootPath):
    from SketchRoot import Require

    ReceiptBytes = ReadPinned(RootPath, "receipt.json")
    Require(Sha256(ReceiptBytes).hexdigest(), KReceiptDigest, "pinned p04 receipt")
    Receipt = Json.loads(ReceiptBytes)
    Require(
        (Receipt["recipe_id"], Receipt["measurements"], bool(Receipt["errors"])),
        ("P04", "measurements.json", False),
        "qualified p04 receipt",
    )
    MeasuredBytes = ReadPinned(RootPath, "measurements.json")
    Require(
        Sha256(MeasuredBytes).hexdigest(),
        Receipt["measurement_receipt_sha256"],
        "independent measurement digest",
    )
    Measured = Json.loads(MeasuredBytes)
    Require(
        (
            Measured["recipe_id"],
            Measured["executable_file_version"],
            bool(Measured["errors"]),
        ),
        ("P04", KApplicationBuild, False),
        "measured build and capture status",
    )
    Require(Measured["saves"], Receipt["native_files"], "measurement save inventory")
    Require(
        Measured["reopen_process_id"] != Measured["authoring_process_id"],
        True,
        "independent native reopen",
    )
    Names = {Asset["file"] for Asset in Receipt["native_files"]}
    Reopened = Measured["observations"]["reopened_files"]
    Require(set(Reopened), Names, "independent reopen inventory")
    Require(
        (len(Receipt["native_files"]), len(Names)),
        (11, 11),
        "complete discovery capture count",
    )
    return Receipt, Reopened


# independent profile observations check numerical values without assuming sketch load order
def CheckLengths(Sketches, Reading):
    from SketchRoot import Require

    Measured = {}
    for Feature in Reading["feature_tree"]:
        if Feature["type"] == "ProfileFeature":
            Measured[Feature["name"]] = {
                Dim["name"]: Dim["system_value"] for Dim in Feature["dimensions"]
            }
    Claimed = set()
    for Sketch in Sketches:
        Actual = {Dim["name"]: Dim["metres"] for Dim in Sketch["length_dimensions"]}
        Require(
            len(Actual), len(Sketch["length_dimensions"]), "unique native length names"
        )
        Matches = [
            NameValue
            for NameValue, Lengths in Measured.items()
            if Lengths.keys() == Actual.keys()
        ]
        Require(len(Matches), 1, "one independently measured length group")
        (NameValue,) = Matches
        Require(NameValue not in Claimed, True, "distinct measured groups")
        Claimed.add(NameValue)
        Errors = {
            Name: abs(Value - Measured[NameValue][Name])
            for Name, Value in Actual.items()
        }
        Require(
            all(Delta <= 1e-9 for Delta in Errors.values()),
            True,
            f"measured lengths for {NameValue}",
        )
        Sketch["measurement_profile"] = NameValue
        Sketch["length_error_metres"] = Errors
    Require(Claimed, set(Measured), "all measured profile length groups")


# reopened native relations independently check axis codes and their member targets
def CheckMemberRelations(Sketches, Reading):
    from SketchReader import KAxisRelations
    from SketchRoot import Require

    ByName = {Sketch["name"]: Sketch for Sketch in Reading["sketches"]}
    for Sketch in Sketches:
        NameValue = Sketch["measurement_profile"]
        Measured = []
        for Relation in ByName[NameValue]["relations"]:
            if Relation["type"] in KAxisRelations and Relation["entity_types"] == [3]:
                (Segment,) = Relation["entities"]
                Require(Segment["segment_type"], 0, "independently measured line")
                Measured.append((Relation["type"], tuple(Segment["id"])))
        Decoded = [
            (Relation["type_code"], (Relation["segment_native_id"],) * 2)
            for Relation in Sketch["member_relations"]
        ]
        Require(
            sorted(Decoded),
            sorted(Measured),
            f"measured line relations for {NameValue}",
        )


# scalar lengths and preserved operand identities must both agree with native reopening
def CheckDimensionOperands(Sketches, Reading):
    from SketchRoot import Require

    ByName = {Sketch["name"]: Sketch for Sketch in Reading["sketches"]}
    AxisClasses = {"sgPntPntHorDist": 0, "sgPntPntVertDist": 1}
    for Sketch in Sketches:
        NameValue = Sketch["measurement_profile"]
        Points = Sketch["points_metres"]
        Expected = Counter()
        MeasuredTallies = Counter()
        for Relation in ByName[NameValue]["relations"]:
            for Entity, TypeValue in zip(
                Relation["entities"], Relation["entity_types"], strict=True
            ):
                if TypeValue == 2:
                    MeasuredTallies[tuple(Entity["id"])] += 1
            if Relation["type"] != 1:
                continue
            Require(Relation["entity_types"], [2, 2], "native distance point operands")
            Expected[tuple(tuple(Point["id"]) for Point in Relation["entities"])] += 1
            for Point in Relation["entities"]:
                Index, _ = Point["id"]
                Native = tuple(
                    float(Coordinate) / 1000 for Coordinate in Point["point_local_mm"]
                )
                Local = (*Points[Index], 0.0)
                Require(
                    all(abs(A - B) <= 1e-9 for A, B in zip(Local, Native, strict=True)),
                    True,
                    "native distance operand coordinates",
                )
        Actual = Counter()
        DistanceTallies = Counter()
        for Dim in Sketch["length_dimensions"]:
            Operands = tuple(Dim["point_native_ids"])
            Actual[Operands] += 1
            DistanceTallies.update(Operands)
            Start, End = (Points[Index] for Index, _ in Operands)
            Delta = tuple(abs(A - B) for A, B in zip(Start, End, strict=True))
            Axis = AxisClasses.get(Dim["class"])
            Distance = Hypot(*Delta) if Axis is None else Delta[Axis]
            Require(
                abs(Distance - Dim["metres"]) <= 1e-9, True, "decoded operand distance"
            )
        Require(
            Actual, Expected, f"measured ordered dimension bindings for {NameValue}"
        )
        SavedTallies = Counter(
            {Row["id"]: Row["tally"] for Row in Sketch["point_relation_tallies"]}
        )
        Require(
            SavedTallies,
            MeasuredTallies,
            f"measured point incidence counts for {NameValue}",
        )
        Sketch["unmapped_point_relation_tallies"] = [
            {"id": Identity, "tally": Tally}
            for Identity, Tally in sorted((SavedTallies - DistanceTallies).items())
        ]


# point incidence counts agree with the saved, ordered two-member relations
def CheckCoincidence(Sketches, Reading):
    from SketchRoot import Require

    ByName = {Sketch["name"]: Sketch for Sketch in Reading["sketches"]}
    for Sketch in Sketches:
        NameValue = Sketch["measurement_profile"]
        Expected = []
        for Relation in ByName[NameValue]["relations"]:
            if Relation["type"] == 9:
                Require(
                    Relation["entity_types"],
                    [2, 2],
                    "native coincidence point operands",
                )
                Expected.append([tuple(Point["id"]) for Point in Relation["entities"]])
        Actual = [
            Row["point_native_ids"]
            for Row in Sketch["point_coincidences"]
            if not Row["suppressed"] and not Row["deleted"]
        ]
        Require(
            Actual, Expected, f"measured ordered coincidence operands for {NameValue}"
        )
        Require(
            Counter(Point for Operands in Actual for Point in Operands),
            Counter(
                {
                    Row["id"]: Row["tally"]
                    for Row in Sketch["unmapped_point_relation_tallies"]
                }
            ),
            f"coincidence accounts for point incidences in {NameValue}",
        )
        Sketch["unmapped_point_relation_tallies"] = []


# exact native blob checks keep witness based layouts scoped to their discovery inputs
def ReadCapture(RootPath, Asset, Reading, IncludeCoincidence=False):
    from convert.adapters.solidworks.container.Archive import ContainerMo
    from convert.adapters.solidworks.container.Container import SldprtArchive
    from SketchReader import ReadSketches
    from SketchRoot import KGeneration, Require

    FileName = Asset["file"]
    Require(
        bool(Regex.fullmatch(r"P04-solidworks-[A-Za-z0-9_-]+\.SLDPRT", FileName)),
        True,
        "p04 capture filename",
    )
    Native = ReadPinned(RootPath, FileName)
    Digest = Sha256(Native).hexdigest()
    Require(
        (Digest, len(Native)),
        (Asset["sha256"], Asset["size_bytes"]),
        f"verified capture {FileName}",
    )
    Require(
        (
            Asset["save_errors"],
            Asset["save_warnings"],
            any(Reading["open_status"].values()),
        ),
        (0, 0, False),
        f"verified native open {FileName}",
    )
    Container = SldprtArchive.from_bytes(Native, FileName)
    Require(ContainerMo(Container.streams), KGeneration, "model generation")
    Contents = Container.require("Contents/Config-0")
    Sketches, Manager = ReadSketches(Contents, KApplicationBuild, IncludeCoincidence)
    CheckLengths(Sketches, Reading)
    CheckMemberRelations(Sketches, Reading)
    CheckDimensionOperands(Sketches, Reading)
    if IncludeCoincidence:
        CheckCoincidence(Sketches, Reading)
    return {
        "file": FileName,
        "native_sha256": Digest,
        "config_sha256": Sha256(Contents).hexdigest(),
        "relation_manager": Manager,
        "sketches": Sketches,
    }


# stdout is an interoperable evidence receipt for downstream comparison tooling
def MainEntry():
    Parser = ArgumentParser(description=__doc__)
    Parser.add_argument(
        "--include-coincidence",
        action="store_true",
        help="verify saved two-point relations",
    )
    Arguments = Parser.parse_args()
    RootPath = Path(__file__).resolve().parents[3]
    ImportPaths.insert(0, str(RootPath / "src"))
    Receipt, Reopened = ReadReceipts(RootPath)
    Captures = [
        ReadCapture(
            RootPath, Asset, Reopened[Asset["file"]], Arguments.include_coincidence
        )
        for Asset in Receipt["native_files"]
    ]
    Evidence = {
        "scope": "p04_discovery_research",
        "capture_revision": KCaptureRev,
        "capture_receipt_sha256": KReceiptDigest,
        "measurements_sha256": Receipt["measurement_receipt_sha256"],
        "application_build": KApplicationBuild,
        "captures": Captures,
    }
    Text = Json.dumps(Evidence, sort_keys=True, indent=2, allow_nan=False)
    StandardOutput.buffer.write((Text + "\n").encode("utf-8"))


if __name__ == "__main__":
    MainEntry()
