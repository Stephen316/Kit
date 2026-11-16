"""Compare resolved P01 and P03 principal rectangles with pinned native readbacks."""

from argparse import ArgumentParser
import json
import math
from pathlib import Path
import sys

REVISION = "89c25945f5833ad9c3a1c6c683df510b5702dd54"
SPECIFICATION_SHA256 = (
    "3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf"
)
CAPTURES = {"P01": ("75b9308cf13e", 6), "P03": ("db1390476325", 8)}


# the independent API reports directed lines in world coordinates under saved segment IDs
def check_rectangle(rectangle, native, tolerance):
    from SketchRoot import Require

    (sketch,) = [
        sketch for sketch in native["sketches"] if sketch["name"] == rectangle["name"]
    ]
    support = rectangle["support"]
    Require(support["plane_name"], sketch["support_name"], "measured principal support")
    transform = support["transform"]
    basis = transform["basis"] or (1, 0, 0, 0, 1, 0, 0, 0, 1)
    tx, ty, tz, scale = transform["translation_scale"]
    Require(
        (*basis, tx, ty, tz, scale),
        tuple(sketch["model_to_sketch_transform"][:13]),
        "measured placement",
    )

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
    Require(
        (len(edges), len(segments), len(sketch["entities"])),
        (4, 4, 4),
        "four perimeter segments",
    )
    world_lines = []
    for edge in edges:
        native_id = edge["native_id"]
        entity = segments.pop((native_id, native_id))
        Require(
            (entity["type"], entity["construction"]),
            (0, False),
            "measured perimeter line",
        )
        start, end = [points[index] for index in edge["point_indices"]]
        for actual, expected in (
            (start, entity["start_world_mm"]),
            (end, entity["end_world_mm"]),
        ):
            Require(
                math.dist(actual, expected) <= tolerance,
                True,
                "measured directed line endpoint",
            )
        world_lines.append({"id": entity["id"], "start": start, "end": end})

    (feature,) = [
        row
        for row in native["feature_tree"]
        if (row["type"], row["name"]) == ("ProfileFeature", rectangle["name"])
    ]
    measured = {row["name"]: row["system_value"] for row in feature["dimensions"]}
    saved = {row["name"]: row["metres"] for row in geometry["length_dimensions"]}
    Require(len(saved), 2, "two saved rectangle dimensions")
    Require(saved, measured, "measured named dimensions")
    return world_lines


# the saved relation targets must match the independent readback and the typed origin
def check_rectangle_constraints(rectangle, native):
    from SketchEvidence import (
        CheckCoincidence,
        CheckDimensionOperands,
        CheckMemberRelations,
    )
    from SketchRoot import Require

    relation = rectangle["point_coincidence"]
    geometry = {
        **rectangle["geometry"],
        "measurement_profile": rectangle["name"],
        "point_coincidences": [relation],
    }
    CheckMemberRelations([geometry], native)
    CheckDimensionOperands([geometry], native)
    CheckCoincidence([geometry], native)
    origin = rectangle["origin"]
    (proxy,) = rectangle["geometry"]["external_point_references"]
    Require(
        (proxy["feature_id"], proxy["handle_class"], proxy["handle_fields"]),
        (origin["native_feature_id"], "sgPointHandle", (0, -1, 0)),
        "typed origin point reference",
    )
    Require(
        proxy["local_id"] in relation["point_native_ids"],
        True,
        "coincidence uses its external origin proxy",
    )


# committed source and measurement hashes bind each comparison to the same physical part
def build_report(
    root, through_profile=False, through_operation=False, include_coincidence=False
):
    from PairedCaptureIntake import (
        CAPTURES as CAPTURE_PATH,
        SPECIFICATIONS,
        GitSnapshot,
        inspect_capture,
        recipe_roster,
        require,
        sha256,
    )
    from ArchiveVersion import KApplicationBuild
    from RectangularConfig import read_rectangle_configuration
    from P03BossEvidence import (
        check_boss_operation,
        check_boss_witness,
        read_rectangle_boss,
    )
    from RectangularResolved import (
        close_rectangle,
        read_rectangle_entry,
        read_resolved_rectangle,
    )
    from SketchRoot import KGeneration, Require
    from convert.adapters.solidworks.Container.Archive import ContainerMo
    from convert.adapters.solidworks.Container.Container import SldprtArchive

    snapshot = GitSnapshot(root)
    specifications_bytes = snapshot.blob(REVISION, SPECIFICATIONS)
    require(
        sha256(specifications_bytes) == SPECIFICATION_SHA256,
        "pinned specification digest changed",
    )
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
            snapshot,
            REVISION,
            f"{folder}/receipt.json",
            recipes[recipe],
            "solidworks",
            specifications,
            SPECIFICATION_SHA256,
        )
        Require(
            (intake["split"], intake["executable_file_version"]),
            ("discovery", "34.4.1.1011"),
            "pinned discovery build",
        )
        coverage = intake["recording_coverage"]
        Require(
            (
                coverage["readback_count"],
                coverage["clean_load_diagnostic_count"],
                coverage["repeat_save_used_fresh_application_process"],
                len(intake["native_files"]),
            ),
            (count, count, True, count),
            "clean measurements from a fresh native process",
        )
        readbacks = snapshot.document(REVISION, intake["measurements"]["path"])[
            "observations"
        ]["reopened_files"]
        cases = []
        for asset in intake["native_files"]:
            name = asset["path"].rsplit("/", 1)[-1]
            part = snapshot.blob(REVISION, asset["path"])
            Require(sha256(part), asset["sha256"], "native part hash")
            archive = SldprtArchive.from_bytes(part, name)
            Require(
                ContainerMo(archive.streams), KGeneration, "pinned model generation"
            )
            config = archive.require("Contents/Config-0")
            resolved = archive.require("Contents/Config-0-ResolvedFeatures")
            entry, configuration = read_rectangle_configuration(
                config, KApplicationBuild
            )
            config_index = entry.NextIndex
            read_boss = through_operation and recipe == "P03"
            if read_boss:
                cursor, rectangle = read_rectangle_entry(
                    resolved,
                    entry,
                    KApplicationBuild,
                    configuration["atom_count"],
                    include_coincidence=include_coincidence,
                )
                close_rectangle(cursor, rectangle, configuration["atom_count"])
            else:
                rectangle = read_resolved_rectangle(
                    resolved,
                    entry,
                    KApplicationBuild,
                    configuration["atom_count"],
                    through_profile=through_profile or through_operation,
                    include_coincidence=include_coincidence,
                )
            world_lines = check_rectangle(rectangle, readbacks[name], tolerance)
            if include_coincidence:
                check_rectangle_constraints(rectangle, readbacks[name])
            case = {
                "file": name,
                "native_sha256": asset["sha256"],
                "config_sha256": sha256(config),
                "resolved_sha256": sha256(resolved),
                "config_next_map_index": config_index,
                "config": configuration,
                "rectangle": rectangle,
                "perimeter_world_mm": world_lines,
            }
            if read_boss:
                boss = read_rectangle_boss(cursor, rectangle)
                boss["measured_operation_check"] = check_boss_operation(
                    boss,
                    rectangle,
                    world_lines,
                    readbacks[name],
                    specifications["comparison_tolerances"],
                )
                check_boss_witness(case, boss)
                case["boss"] = boss
            cases.append(case)
        report["families"].append(
            {
                "recipe": recipe,
                "measurements": intake["measurements"],
                "captures": cases,
            }
        )
    return report


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--through-profile",
        action="store_true",
        help="close the rectangle and check the next list boundary",
    )
    parser.add_argument(
        "--through-operation",
        action="store_true",
        help="replay the P03 boss through the resolved stream footer",
    )
    parser.add_argument(
        "--include-coincidence",
        action="store_true",
        help="verify the saved coincidence, axis and dimension operands",
    )
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    sys.path[:0] = [str(root / "src"), str(root / "re" / "automation")]
    output = json.dumps(
        build_report(
            root,
            arguments.through_profile,
            arguments.through_operation,
            arguments.include_coincidence,
        ),
        indent=2,
        sort_keys=True,
        allow_nan=False,
    )
    sys.stdout.buffer.write((output + "\n").encode("utf-8"))
