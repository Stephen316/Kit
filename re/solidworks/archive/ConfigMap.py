"""Replay the witnessed P04 presentation suffix on the shared Config-0 map."""

from argparse import ArgumentParser
from hashlib import sha256 as Sha256
import json as Json
from pathlib import Path
from struct import unpack_from as UnpackFrom
from sys import path as ImportPaths
from sys import stdout as StandardOutput

from ArchiveVersion import KApplicationBuild
from SketchEvidence import (
    KCaptureRev,
    KReceiptDigest,
    ReadPinned,
    ReadReceipts,
)

if __name__ == "__main__":
    ImportPaths.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from SketchRoot import KGeneration, Require
from convert.adapters.solidworks.Config.CutConfig import ReadCutConfig
from convert.adapters.solidworks.Container.Container import SldprtArchive


# this research continuation is bounded to the pinned build and witnessed suffix layout
def ReadConfigMap(BlobValue, BuildName):
    Require(BuildName, KApplicationBuild, "witnessed P04 model build")
    Config = ReadCutConfig(BlobValue, KGeneration)
    return Config.Cursor, {
        "start": (Config.RelationEnd, Config.RelationNext),
        "regions": Config.WalkValue["regions"],
        "pointers": Config.WalkValue["pointers"],
    }


# the saved header can corroborate the derived map but never initializes it
def ReportConfigurationMaps(RootPath):
    Receipt, _ = ReadReceipts(RootPath)
    Results = []
    for Capture in Receipt["native_files"]:
        NameValue = Capture["file"]
        Data = ReadPinned(RootPath, NameValue)
        Require(Sha256(Data).hexdigest(), Capture["sha256"], "pinned Config-0 part")
        Archive = SldprtArchive.from_bytes(Data, NameValue)
        Config = Archive.require("Contents/Config-0")
        Resolved = Archive.require("Contents/Config-0-ResolvedFeatures")
        Cursor, Walk = ReadConfigMap(Config, KApplicationBuild)
        (Header,) = UnpackFrom("<I", Resolved)
        Require(Cursor.NextIndex, Header, "derived map and P04 resolved header")
        Results.append(
            {
                "capture": NameValue,
                "sha256": Sha256(Config).hexdigest(),
                "end": Cursor.Offset,
                "next_map_index": Cursor.NextIndex,
                "sketch_objects": [
                    Slot for Slot, Name in Cursor.Objects.items() if Name == "sgSketch"
                ],
                **Walk,
            }
        )
    return {
        "scope": "p04_discovery_config_map",
        "capture_revision": KCaptureRev,
        "capture_receipt_sha256": KReceiptDigest,
        "application_build": KApplicationBuild,
        "captures": Results,
    }


if __name__ == "__main__":
    Parser = ArgumentParser(description=__doc__)
    Parser.parse_args()
    RootPath = Path(__file__).resolve().parents[3]
    Evidence = ReportConfigurationMaps(RootPath)
    Text = Json.dumps(Evidence, sort_keys=True, indent=2, allow_nan=False)
    StandardOutput.buffer.write((Text + "\n").encode("utf-8"))
