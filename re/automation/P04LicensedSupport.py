"""Compare the public SOLIDWORKS P04 cap with licensed observations."""

import argparse
import math
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from Corpus import git as run_git
from CutHistoryGraph import plane_metrics, read_history, unique
from P04FinalBodyEvidence import (
    REVISION,
    SOLIDWORKS_BUILD,
    SPECIFICATION,
    SPECIFICATION_SHA256,
    licensed_readback,
    solidworks_capture,
)
from PairedCaptureIntake import GitSnapshot, require, sha256
from Records import canonical
from convert.api.ApiOpen import OpenDocument

AREA_TOLERANCE_MM2 = 1e-8


def perimeter_area(perimeter, normal):
    def cross_component(index):
        left, right = (index + 1) % 3, (index + 2) % 3
        return math.fsum(
            start[left] * end[right] - start[right] * end[left]
            for _, (start, end) in perimeter
        )

    return abs(math.fsum(value * cross_component(axis) for axis, value in enumerate(normal))) / 2


def measured_support(phase):
    face = phase["support"]
    sketch = unique(
        (item for item in phase["sketches"] if item["feature"]["name"] == "CutSketch"),
        "licensed CutSketch",
    )
    matrix = sketch["model_to_sketch_transform"]
    axis = [matrix[index] for index in (2, 5, 8)]
    require(
        face["verified"] is True
        and face["roundtrip_same_face"] is True
        and face["same_as_expected_boss"] is True
        and len(matrix) == 16
        and matrix[12] == 1
        and math.dist(axis, face["normal_world"]) <= 1e-9,
        "licensed support does not agree with the measured unit sketch transform",
    )
    area = face["area_m2"] * 1e6
    require(math.isfinite(area) and area > 0, "invalid licensed cap area")
    return {
        "measured_normal": face["normal_world"],
        "offset_mm": -1000 * matrix[11],
        "visible_cap_area_mm2": area,
        "owner_native_id": face["oldest_owning_feature"]["id"],
    }


def licensed_cases(directory, receipt_digest):
    head = run_git(ROOT, "rev-parse", "HEAD").decode().strip()
    require(
        not run_git(ROOT, "status", "--porcelain", "--", "src", "re/automation"),
        "use a clean reader and research source checkout",
    )
    snapshot = GitSnapshot(ROOT)
    raw_specification = snapshot.blob(REVISION, SPECIFICATION)
    require(sha256(raw_specification) == SPECIFICATION_SHA256, "corpus specification digest differs")
    specification = snapshot.parse_document(raw_specification, SPECIFICATION)
    capture = solidworks_capture(snapshot, specification)
    source, measurements_digest, observations = licensed_readback(
        snapshot, capture, directory, receipt_digest
    )
    provenance = {
        "reader_revision": head,
        "solidworks_build": SOLIDWORKS_BUILD,
        "licensed_receipt_sha256": receipt_digest,
        "licensed_measurements_sha256": measurements_digest,
        "licensed_collector_revision": source,
        "capture_revision": REVISION,
    }
    return provenance, specification["comparison_tolerances"], saved_cases(snapshot, capture, observations)


def saved_cases(snapshot, capture, observations):
    for asset in capture["native_files"]:
        raw = snapshot.blob(REVISION, asset["path"])
        require(sha256(raw) == asset["sha256"], "saved P04 archive digest differs")
        graph = read_history(OpenDocument(raw, SourceFormat="solidworks.sldprt", StrictMode=False))
        yield asset, graph, observations[PurePosixPath(asset["path"]).name]


def report(directory, receipt_digest):
    provenance, tolerances, cases = licensed_cases(directory, receipt_digest)
    rows = []
    for asset, graph, native in cases:
        normal, offset = plane_metrics(graph.cut.plane)
        area = perimeter_area(graph.base.perimeter, normal) - perimeter_area(graph.cut.perimeter, normal)
        require(area > 0, "the upper face must remain after the cut")
        phases = {}
        for label in ("before_rebuild", "after_rebuild"):
            face = measured_support(native[label])
            require(
                face["owner_native_id"] == graph.support.query["native_source_id"]
                and math.dist(normal, face["measured_normal"]) <= tolerances["angle_rad_absolute"]
                and abs(offset - face["offset_mm"]) <= tolerances["length_mm_absolute"]
                and abs(area - face["visible_cap_area_mm2"]) <= AREA_TOLERANCE_MM2,
                f"{asset['variant']} {label}: saved support differs from the licensed measurement",
            )
            phases[label] = face
        rows.append({
            "variant": asset["variant"],
            "sha256": asset["sha256"],
            "neutral_plane_normal": normal,
            "neutral_plane_offset_mm": offset,
            "perimeter_derived_area_mm2": area,
            "native": phases,
        })
    return {
        "scope": "solidworks_a04c_saved_support_vs_licensed_measurement",
        **provenance,
        "area_tolerance_mm2": AREA_TOLERANCE_MM2,
        "cases": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readback_directory", type=Path)
    parser.add_argument("--receipt-sha256", required=True)
    args = parser.parse_args()
    sys.stdout.buffer.write((canonical(report(args.readback_directory, args.receipt_sha256)) + "\n").encode())
