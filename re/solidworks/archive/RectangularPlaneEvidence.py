"""Compare resolved P01 and P03 principal rectangles with pinned native readbacks."""

import json
import math
from pathlib import Path
import sys


REVISION = "89c25945f5833ad9c3a1c6c683df510b5702dd54"
SPECIFICATION_SHA256 = "3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf"
CAPTURES = {"P01": ("75b9308cf13e", 6), "P03": ("db1390476325", 8)}


def check_rectangle(rectangle, native, tolerance):
    from SketchRoot import Require

    sketch, = [sketch for sketch in native["sketches"] if sketch["name"] == rectangle["name"]]
    support = rectangle["support"]
    Require(support["plane_name"], sketch["support_name"], "measured principal support")
    transform = support["transform"]
    basis = transform["basis"] or (1, 0, 0, 0, 1, 0, 0, 0, 1)
    tx, ty, tz, scale = transform["translation_scale"]
    Require((*basis, tx, ty, tz, scale), tuple(sketch["model_to_sketch_transform"][:13]), "measured placement")

    geometry = rectangle["geometry"]
    points = [
        [
            1000 * (scale * (basis[row] * x + basis[row + 1] * y) + translation)
            for row, translation in zip((0, 3, 6), (tx, ty, tz), strict=True)
        ]
        for x, y in geometry["points_metres"]
    ]
    edges = [line for line in geometry["lines"] if line["native_id"] >= 0]
    segments = {tuple(entity["id"]): entity for entity in sketch["entities"]}
    Require((len(edges), len(segments), len(sketch["entities"])), (4, 4, 4), "four perimeter segments")
    world_lines = []
    for edge in edges:
        native_id = edge["native_id"]
        entity = segments.pop((native_id, native_id))
        Require((entity["type"], entity["construction"]), (0, False), "measured perimeter line")
        start, end = [points[index] for index in edge["point_indices"]]
        for actual, expected in ((start, entity["start_world_mm"]), (end, entity["end_world_mm"])):
            Require(math.dist(actual, expected) <= tolerance, True, "measured directed line endpoint")
        world_lines.append({"id": entity["id"], "start": start, "end": end})

    feature, = [
        row for row in native["feature_tree"] if (row["type"], row["name"]) == ("ProfileFeature", rectangle["name"])
    ]
    measured = {row["name"]: row["system_value"] for row in feature["dimensions"]}
    saved = {row["name"]: row["metres"] for row in geometry["length_dimensions"]}
    Require(len(saved), 2, "two saved rectangle dimensions")
    Require(saved, measured, "measured named dimensions")
    return world_lines


def build_report(root):
    from PairedCaptureIntake import CAPTURES as CAPTURE_PATH, SPECIFICATIONS, GitSnapshot, inspect_capture, recipe_roster, require, sha256
    from RectangularConfig import KApplicationBuild, read_rectangle_configuration
    from RectangularResolved import read_resolved_rectangle
    from SketchRoot import KGeneration, Require
    from convert.adapters.solidworks.container.Archive import ContainerMo
    from convert.adapters.solidworks.container.Container import SldprtArchive

    snapshot = GitSnapshot(root)
    specifications_bytes = snapshot.blob(REVISION, SPECIFICATIONS)
    require(sha256(specifications_bytes) == SPECIFICATION_SHA256, "pinned specification digest changed")
    specifications = snapshot.parse_document(specifications_bytes, SPECIFICATIONS)
    recipes = recipe_roster(specifications)
    tolerance = specifications["comparison_tolerances"]["length_mm_absolute"]
    report = {
        "scope": "p01_p03_rectangular_plane_research",
        "capture_revision": REVISION,
        "application_build": KApplicationBuild,
        "position_tolerance_mm": tolerance,
        "families": [],
    }
    for recipe, (capture, count) in CAPTURES.items():
        folder = f"{CAPTURE_PATH}{recipe}/solidworks-{capture}"
        intake = inspect_capture(
            snapshot, REVISION, f"{folder}/receipt.json", recipes[recipe], "solidworks", specifications, SPECIFICATION_SHA256
        )
        Require((intake["split"], intake["executable_file_version"]), ("discovery", "34.4.1.1011"), "pinned discovery build")
        coverage = intake["recording_coverage"]
        Require(
            (coverage["readback_count"], coverage["clean_load_diagnostic_count"],
             coverage["repeat_save_used_fresh_application_process"], len(intake["native_files"])),
            (count, count, True, count),
            "clean measurements from a fresh native process",
        )
        readbacks = snapshot.document(REVISION, intake["measurements"]["path"])["observations"]["reopened_files"]
        cases = []
        for asset in intake["native_files"]:
            name = asset["path"].rsplit("/", 1)[-1]
            part = snapshot.blob(REVISION, asset["path"])
            Require(sha256(part), asset["sha256"], "native part hash")
            archive = SldprtArchive.from_bytes(part, name)
            Require(ContainerMo(archive.streams), KGeneration, "pinned model generation")
            config = archive.require("Contents/Config-0")
            resolved = archive.require("Contents/Config-0-ResolvedFeatures")
            entry, configuration = read_rectangle_configuration(config, KApplicationBuild)
            config_index = entry.NextIndex
            rectangle = read_resolved_rectangle(resolved, entry, KApplicationBuild, configuration["atom_count"])
            world_lines = check_rectangle(rectangle, readbacks[name], tolerance)
            cases.append({
                "file": name,
                "native_sha256": asset["sha256"],
                "config_sha256": sha256(config),
                "resolved_sha256": sha256(resolved),
                "config_next_map_index": config_index,
                "config": configuration,
                "rectangle": rectangle,
                "perimeter_world_mm": world_lines,
            })
        report["families"].append({"recipe": recipe, "measurements": intake["measurements"], "captures": cases})
    return report


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root / "src"), str(root / "re" / "automation")]
    output = json.dumps(build_report(root), indent=2, sort_keys=True, allow_nan=False)
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))
