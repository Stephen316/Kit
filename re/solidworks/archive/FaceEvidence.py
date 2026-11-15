"""Replay the P04 cut-face reader at the two observed typed support boundaries."""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import sys

from SketchEvidence import (
    KApplicationBuild,
    KCaptureRev,
    KReceiptDigest,
    ReadPinned,
    ReadReceipts,
)

# earlier archive entries are replay inputs because this reader starts in the support body
CLASSES = {
    43: "moUnitComponent_c",
    350: "moFR_c",
    372: "moFaceRef_c",
    374: "moEndFaceSurfIdRep_c",
    377: "moFromSktEntSurfIdRep_c",
}
OBJECTS = {2: "moPart_c", 353: "moExtObject_c"}

# these stream digests bind the replay anchors to the licensed support observations
WINDOWS = {
    "P04-solidworks-baseline-a.SLDPRT": {
        "sha256": "996ed9d0337cdf8c65927645a2541a93d12c9354300975bbda731bde6829ea31",
        "map_witness_sha256": "b42c9fa8fbc0cc5e2799e3d49a9f1717ae213ca8c12939ab4a5ecf7c4bfd40d9",
        "plane_data_start": 11927,
        "support_end": 12588,
        "face_span": (12200, 12366),
        "normal_world": (0, 0, 1),
        "time_word": 1794688208,
        "ordered_edges": [4, 1, 2, 3],
    },
    "P04-solidworks-plane-yz.SLDPRT": {
        "sha256": "51c8c1f73939541a2e33fa084524591c2f34dc6e4f13028f411cdd35114cc53c",
        "map_witness_sha256": "7a6c1606db89f17e6bd626df49419cc791ff66971ca9699f3e150d30002f3124",
        "plane_data_start": 11991,
        "support_end": 12724,
        "face_span": (12336, 12502),
        "normal_world": (1, 0, 0),
        "time_word": 1794688341,
        "ordered_edges": [4, 3, 2, 1],
    },
}


# native readback supplies an independent identity and orientation check for each boundary
def check_witness(result, witness):
    from SketchRoot import Require

    Require(result["next_map_index"], 475, "support return allocation counter")
    Require(result["plane_data_object"], 460, "plane-data map index")
    Require(result["component"]["object_index"], 462, "component-face map index")
    Require(
        result["plane"]["normal_world"],
        witness["normal_world"],
        "readback support normal",
    )
    face = result["component"]["occurrence"]
    Require(face["object_index"], 464, "face-reference map index")
    Require(
        (face["offset"], face["end"]), witness["face_span"], "native face read span"
    )
    primary = face["primary"]
    Require(
        (primary["feature_id"], primary["time_word"], primary["occurrence"]),
        (34, witness["time_word"], 1),
        "persistent end face tuple",
    )
    Require(
        [edge["occurrence"] for edge in face["ordered_edges"]],
        witness["ordered_edges"],
        "ordered persistent boundary occurrences",
    )


# the save receipt and complete resolved digest guard the witnessed data and archive indices
def read_capture(root, asset, reading, witness):
    from convert.adapters.solidworks.container.Archive import ContainerMo
    from convert.adapters.solidworks.container.Container import SldprtArchive
    from FaceOccurrence import read_owned_face
    from SketchRoot import KGeneration, Require

    name = asset["file"]
    native = ReadPinned(root, name)
    digest = sha256(native).hexdigest()
    Require((digest, len(native)), (asset["sha256"], asset["size_bytes"]), name)
    Require(
        (
            asset["save_errors"],
            asset["save_warnings"],
            any(reading["open_status"].values()),
        ),
        (0, 0, False),
        "verified native open",
    )
    container = SldprtArchive.from_bytes(native, name)
    Require(ContainerMo(container.streams), KGeneration, "model generation")
    resolved = container.require("Contents/Config-0-ResolvedFeatures")
    Require(sha256(resolved).hexdigest(), witness["sha256"], "pinned resolved stream")
    result = read_owned_face(
        resolved,
        witness["plane_data_start"],
        witness["support_end"],
        459,
        CLASSES,
        OBJECTS,
    )
    check_witness(result, witness)
    return {
        "file": name,
        "native_sha256": digest,
        "resolved_sha256": witness["sha256"],
        "map_witness_sha256": witness["map_witness_sha256"],
        "support": result,
    }


# the offline receipt keeps the witnessed fields available for later semantic comparisons
def main():
    ArgumentParser(description=__doc__).parse_args()
    root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root / "src"))
    receipt, reopened = ReadReceipts(root)
    assets = {asset["file"]: asset for asset in receipt["native_files"]}
    captures = [
        read_capture(root, assets[name], reopened[name], witness)
        for name, witness in WINDOWS.items()
    ]
    evidence = {
        "scope": "p04_face_support_research",
        "capture_revision": KCaptureRev,
        "capture_receipt_sha256": KReceiptDigest,
        "measurements_sha256": receipt["measurement_receipt_sha256"],
        "application_build": KApplicationBuild,
        "captures": captures,
    }
    output = json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False)
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
