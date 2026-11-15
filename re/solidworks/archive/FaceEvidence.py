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
    320: "moRefPlane_c",
    338: "moCompRefPlane_c",
    344: "moSketchChain_c",
    350: "moFR_c",
    372: "moFaceRef_c",
    374: "moEndFaceSurfIdRep_c",
    377: "moFromSktEntSurfIdRep_c",
}

# these three existing objects establish the sketch owner and filed reference context
OBJECTS = {2: "moPart_c", 74: "sgSketch", 353: "moExtObject_c"}

# these stream digests bind the replay anchors to the licensed support observations
WINDOWS = {
    "P04-solidworks-baseline-a.SLDPRT": {
        "sha256": "996ed9d0337cdf8c65927645a2541a93d12c9354300975bbda731bde6829ea31",
        "map_witness_sha256": "b42c9fa8fbc0cc5e2799e3d49a9f1717ae213ca8c12939ab4a5ecf7c4bfd40d9",
        "sketch_reference": 9600,
        "body_return": 10906,
        "support_start": 11531,
        "native_atom": (11777, 11801, 11889),
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
        "sketch_reference": 9670,
        "body_return": 10970,
        "support_start": 11595,
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
    from FaceOccurrence import FaceCursor
    from ProfileSupport import read_profile_support
    from SketchRoot import KGeneration, Require
    from SupportPlane import read_reference_plane

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
    start, end = witness["sketch_reference"], witness["support_end"]
    Require(0 <= start < end <= len(resolved), True, "bounded profile support")
    cursor = FaceCursor(resolved[:end], start, 418, dict(CLASSES), dict(OBJECTS))
    profile = read_profile_support(cursor)
    Require(profile["sketch_object"], 74, "licensed cut sketch object")
    Require(
        profile["kernel_packet"]["end"],
        witness["body_return"],
        "licensed refill boundary",
    )
    Require(profile["next_map_index"], 456, "licensed support entry counter")
    Require(
        profile["support_offset"], witness["support_start"], "licensed support token"
    )
    prefix = read_reference_plane(cursor, context=0)
    Require(cursor.position, end, "exact enclosing support return")
    Require(
        prefix["plane_data_start"],
        witness["plane_data_start"],
        "licensed plane data start",
    )
    Require(prefix["ref_plane_object"], 458, "reference plane allocation")
    if "native_atom" in witness:
        first, last = prefix["atom_span"]
        observed = first, prefix["atom_arrays_offset"], last
        Require(observed, witness["native_atom"], "licensed reference atom boundaries")
    result = prefix.pop("face")
    check_witness(result, witness)
    primary = result["component"]["occurrence"]["primary"]
    for edge in profile["edge_references"]:
        for key in ("file_ref_object", "feature_id", "time_word", "occurrence"):
            Require(
                edge["primary"][key],
                primary[key],
                f"same profile edge and supporting cap {key}",
            )
    return {
        "file": name,
        "native_sha256": digest,
        "resolved_sha256": witness["sha256"],
        "map_witness_sha256": witness["map_witness_sha256"],
        "profile": profile,
        "support_prefix": prefix,
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
        "support_context_witness_sha256": "00d522c9f5f0cb6e3409139b2ed61286d99ead92f844b6e37a361447f89b7b6e",
        "captures": captures,
    }
    output = json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False)
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
