"""Report typed sketch geometry from the eleven pinned P04 discovery captures."""

from argparse import ArgumentParser
from hashlib import sha256 as Sha256
import json as Json
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


# exact native blob checks keep witness based layouts scoped to their discovery inputs
def ReadCapture(RootPath, Asset, Reading):
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
    Sketches = ReadSketches(Contents, KApplicationBuild)
    CheckLengths(Sketches, Reading)
    return {
        "file": FileName,
        "native_sha256": Digest,
        "config_sha256": Sha256(Contents).hexdigest(),
        "sketches": Sketches,
    }


# stdout is an interoperable evidence receipt for downstream comparison tooling
def MainEntry():
    Parser = ArgumentParser(description=__doc__)
    Parser.parse_args()
    RootPath = Path(__file__).resolve().parents[3]
    ImportPaths.insert(0, str(RootPath / "src"))
    Receipt, Reopened = ReadReceipts(RootPath)
    Captures = [
        ReadCapture(RootPath, Asset, Reopened[Asset["file"]])
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
