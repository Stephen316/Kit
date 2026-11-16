"""Compare a copied licensed SOLIDWORKS run with the pinned P01/P03 captures."""

from argparse import ArgumentParser
from collections import Counter
import json
import math
from pathlib import Path, PureWindowsPath
import re
import sys

from PairedCaptureIntake import GitSnapshot, inspect_capture, recipe_roster, require, sha256

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(Path(__file__).with_name("ApplicationWorkers"))]

from ApplicationProtocol import encoded
from convert.adapters.solidworks.Container.Archive import ArchiveError, ContainerMo
from convert.adapters.solidworks.Container.Container import SldprtArchive
from convert.adapters.solidworks.Container.PlaneBasis import KUnitRows
from convert.adapters.solidworks.Resolved.RectanglePart import ReadRectPart

CAPTURE_REVISION = "89c25945f5833ad9c3a1c6c683df510b5702dd54"
CAPTURES = {
    "P01": ("75b9308cf13e", "3c389fe4069bece7ecf64f0294d111ce7f44131b2fc576d3f2ac4291e0fec7bf", 6),
    "P03": ("db1390476325", "f2308ae749f3d739746301873a49e997e2cf494f9d459e954403b66b17e22a94", 8),
}
SPEC = "re/automation/PairSpecs.json"
SPEC_DIGEST = "3c93e024f9fbdda50e610bda3b363bf30e8e7cdc914ef0728087befe129951bf"
AUTHORING = "re/automation/PairedCaptures/SolidWorksAuthoring"
CONTROL = "re/solidworks/examples/.SLDPRT/example.SLDPRT"
CONTROL_DIGEST = "d1bbca099ccac1330024619390df3c6b76320a6a6c281a5009578b2fb63e7408"
OPERATION = "p01-p03-readback"
BUILD = "34.4.1.1011"

# principal field coverage depends on the exact sources compiled for the readback
COLLECTORS = {
    "1c58fcdec0b20e4a2fac86564466a735f2abb81654090bee381a62c43553aa21": (False, None),
    "16e4f1331adaba840dcfe57f81f5614ddff726c9505f1d281a706f56a2845c95": (True, None),
    "82f988d46f463963cd2ec377966dcdcd268c1b699a7d6e24246ab525a086dd9d": (
        True,
        {
            "launcher": "492dd92a76427b687d16587c3c2277150c7d2befaf275d9459230534463c9530",
            "circle_collector": "b674dd765c133a53efd87da406ce9ec6cbcf218b25a2ee3329228eeee61a5023",
        },
    ),
}
DOCUMENTS = ("plan", "measurements", "receipt")
PHASES = ("before_rebuild", "after_rebuild")
CLEAN_OPEN = {"document_returned": True, "errors": 0, "warnings": 0}


def read_bytes(path, limit):
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    require(len(data) <= limit, "copied readback input exceeds the byte limit")
    return data


def read_dispatch(directory, digest):
    dispatch_bytes = read_bytes(directory / "dispatch.json", 1024 * 1024)
    require(sha256(dispatch_bytes) == digest, "dispatch digest mismatch")
    dispatch = GitSnapshot.parse_document(dispatch_bytes, "dispatch")
    revision = dispatch["source_revision"]
    proof = dispatch["proof"]
    require(
        re.fullmatch(r"[0-9a-f]{40}", revision)
        and dispatch["version"] == 1
        and dispatch["status"] == "completed"
        and dispatch["provider"] == "dassault.solidworks.com"
        and proof["claim"] == "unqualified_application_observation"
        and proof["phase"] == OPERATION
        and proof["solidworks_build"] == BUILD
        and proof["plan_sha256"]
        == sha256(encoded({"operation": OPERATION, "source_revision": revision})),
        "dispatch does not bind a completed principal readback phase",
    )
    flat = {name: directory / f"readback.{name}.json" for name in DOCUMENTS}
    nested = {name: directory / "readback" / f"{name}.json" for name in DOCUMENTS}
    layouts = [
        layout for layout in (flat, nested) if any(path.exists() for path in layout.values())
    ]
    require(len(layouts) == 1, "expected one copied readback output layout")
    files = dispatch["files"]
    require(
        set(files) == {f"readback.{name}" for name in DOCUMENTS}, "dispatch file roster mismatch"
    )
    records, digests = {}, {}
    for name, path in layouts[0].items():
        content = read_bytes(path, 32 * 1024 * 1024)
        digests[name] = sha256(content)
        require(
            files[f"readback.{name}"]
            == {
                "path": f"readback/{name}.json",
                "sha256": digests[name],
                "size_bytes": len(content),
            },
            f"dispatch file pin mismatch for {name}",
        )
        records[name] = GitSnapshot.parse_document(content, name)
    plan, measurements, receipt = (records[name] for name in DOCUMENTS)
    require(
        (plan["source_revision"], plan["recipe"]) == (revision, "P01-P03")
        and measurements["schema"] == 1
        and measurements["claim"] == "supplemental_native_observation"
        and measurements["source_bytes_verified_after_readback"] is True
        and measurements["plan_sha256"] == proof["readback_plan_sha256"] == digests["plan"]
        and receipt
        == {
            "schema": 1,
            "status": "observed",
            "plan_sha256": digests["plan"],
            "measurements_sha256": digests["measurements"],
            "observed_files": 14,
            "principal_profiles_observed": 14,
        },
        "plan, measurements and receipt do not bind the same completed suite",
    )
    return dispatch, plan, measurements["run"], digests


def verify_owner(run, dispatch):
    owner, app = run["native_owner"], run["application"]
    require(
        run["status"] == "observed"
        and run["owned_process_exit_observed"] is True
        and not run.get("cleanup_diagnostics")
        and owner["version"] == 1
        and owner["initial_documents"] == 0
        and owner["source_revision"] == dispatch["source_revision"]
        and owner["request_sha256"] == dispatch["request_sha256"]
        and sha256(encoded(owner)) == dispatch["proof"]["native_owner_sha256"]
        and owner["build"] == app["build"] == BUILD
        and app["revision"] == BUILD.rsplit(".", 1)[0]
        and owner["pid"] == app["pid"] > 0
        and owner["session"] == app["session_id"] >= 0
        and re.fullmatch(r"windows:[1-9][0-9]+", owner["created"])
        and PureWindowsPath(owner["image"]).name.casefold() == "sldworks.exe"
        and PureWindowsPath(app["resolved_executable"])
        == PureWindowsPath(app["expected_resolved_executable"]),
        "fresh SOLIDWORKS run lacks exact request ownership or observed exit",
    )


def git_pin(snapshot, revision, path):
    data = snapshot.blob(revision, path)
    return {
        "path": path,
        "git_blob": snapshot.tree(revision)[path],
        "sha256": sha256(data),
        "size_bytes": len(data),
    }


def read_sources(snapshot, plan):
    revision = plan["source_revision"]
    sources = {}
    for role, path in (
        ("specification", SPEC),
        ("control", CONTROL),
        ("collector", f"{AUTHORING}/P04Readback.cs"),
        ("launcher", f"{AUTHORING}/ReadP04SolidWorks.ps1"),
    ):
        pin = git_pin(snapshot, revision, path)
        require(pin == plan[role], f"worker {role} differs from its Git source pin")
        sources[role] = pin
    require(
        sources["specification"]["sha256"] == SPEC_DIGEST
        and sources["control"]["sha256"] == CONTROL_DIGEST,
        "worker specification or healthy control differs from the prescribed asset",
    )
    collector_digest = sources["collector"]["sha256"]
    require(collector_digest in COLLECTORS, "unsupported principal collector")
    _, bundle = COLLECTORS[collector_digest]
    if bundle is None:
        require(
            "circle_collector" not in plan,
            "legacy principal collector has an unexpected companion",
        )
    else:
        companion = git_pin(snapshot, revision, f"{AUTHORING}/P02Readback.cs")
        require(
            companion == plan.get("circle_collector")
            and companion["sha256"] == bundle["circle_collector"]
            and sources["launcher"]["sha256"] == bundle["launcher"],
            "worker compiled principal collector bundle differs from the approved sources",
        )
        sources["circle_collector"] = companion
    installed = {}
    for role in ("executable", "interop", "constants"):
        digest = plan[f"installed_{role}_sha256"]
        require(re.fullmatch(r"[0-9a-f]{64}", digest), f"worker lacks installed {role} digest")
        installed[role] = digest
    return sources, installed


def read_captures(snapshot, plan, specs):
    recipes = recipe_roster(specs)
    native_files, captures, controls = {}, {}, []
    require(set(plan["existing_captures"]) == set(CAPTURES), "worker capture families differ")
    for family, (folder, digest, count) in CAPTURES.items():
        receipt_path = f"re/automation/PairedCaptures/{family}/solidworks-{folder}/receipt.json"
        intake = inspect_capture(
            snapshot,
            CAPTURE_REVISION,
            receipt_path,
            recipes[family],
            "solidworks",
            specs,
            SPEC_DIGEST,
        )
        require(
            intake["receipt"]["sha256"] == digest
            and intake["executable_file_version"] == BUILD
            and intake["split"] == "discovery"
            and len(intake["native_files"]) == count
            and intake["recording_coverage"]["repeat_save_used_fresh_application_process"],
            f"historical {family} capture fails its saved native readback pin",
        )
        pins = {
            role: git_pin(snapshot, CAPTURE_REVISION, intake[role]["path"])
            for role in ("receipt", "measurements")
        }
        require(
            pins == plan["existing_captures"][family],
            f"worker {family} capture differs from the original receipts",
        )
        for role, pin in pins.items():
            require(
                git_pin(snapshot, plan["source_revision"], pin["path"]) == pin,
                f"worker revision changes {family} {role} bytes",
            )
        observations = snapshot.document(CAPTURE_REVISION, pins["measurements"]["path"])[
            "observations"
        ]
        controls.extend(observations[f"healthy_control_{phase}"] for phase in ("before", "after"))
        for item in intake["native_files"]:
            name = Path(item["path"]).name
            pin = {key: item[key] for key in ("path", "git_blob", "sha256", "size_bytes")}
            require(
                git_pin(snapshot, plan["source_revision"], pin["path"]) == pin,
                f"worker revision changes {name}",
            )
            native_files[name] = (
                family,
                item["variant"],
                pin,
                observations["reopened_files"][name],
            )
        captures[family] = {**pins, "observed_files": count}
    require(
        plan["native_files"] == {name: row[2] for name, row in native_files.items()},
        "worker native pins differ from the exact historical save roster",
    )
    return native_files, captures, controls


def mm(values):
    return [1000 * value for value in values]


def close_vector(actual, expected, tolerance, label):
    require(len(actual) == len(expected) and math.dist(actual, expected) <= tolerance, label)


def indexed(rows, identity):
    index = {identity(row): row for row in rows}
    require(len(index) == len(rows), "duplicate observed identity")
    return index


def participant(row):
    return tuple(row["id"])


def check_point(row, geometry, owner, tolerance):
    identity = participant(row)
    require(
        row["kind"] == "sketch_point"
        and row["native_sketch_available"] is True
        and row["same_sketch"] is (owner == "RectangleSketch")
        and row["native_sketch_owner"] == owner,
        "sketch point ownership differs",
    )
    local = geometry["points_metres"][identity[0]] if owner == "RectangleSketch" else (0, 0)
    close_vector(mm(row["local_m"]), mm((*local, 0)), tolerance, "typed point coordinates differ")
    return identity


def feature(name, kind, identity):
    return {"name": name, "type": kind, "id": identity, "suppressed": False}


def check_perimeter(stage, history, rectangle, tolerance):
    sketch = stage["sketch"]
    geometry = rectangle.Profile.Geometry
    native = indexed(stage["perimeter"], participant)
    segments = indexed(sketch["segments"], lambda row: participant(row["entity"]))
    archived = {line["native_id"]: line for line in geometry["lines"] if line["native_id"] >= 0}
    historical = indexed(history["entities"], participant)
    require(
        len(native) == 4
        and native.keys() == segments.keys() == historical.keys()
        and native.keys() == {(identity, identity) for identity in archived},
        "perimeter segment roster differs",
    )
    points = geometry["points_metres"]
    identities = set()
    for identity, edge in native.items():
        segment = segments[identity]
        require(
            segment["entity"]
            == {"kind": "sketch_segment", "id": list(identity), "type": 0, "same_sketch": True}
            and segment["construction"] is historical[identity]["construction"] is False
            and historical[identity]["type"] == 0,
            "perimeter uses a non-owned or non-ordinary line",
        )
        for label, index in zip(
            ("start", "end"), archived[identity[0]]["point_indices"], strict=True
        ):
            point = check_point(segment[label], geometry, "RectangleSketch", tolerance)
            require(point[0] == index, "directed endpoint does not select the saved member")
            identities.add(point)
            world = [
                1000
                * sum(
                    axis[coord] * value
                    for axis, value in zip(rectangle.Directions[:2], points[index], strict=True)
                )
                for coord in range(3)
            ]
            close_vector(
                mm(edge[f"{label}_world_m"]),
                world,
                tolerance,
                "world line does not match typed frame",
            )
            close_vector(
                mm(edge[f"{label}_world_m"]),
                historical[identity][f"{label}_world_mm"],
                tolerance,
                "world line differs from the historical reopen",
            )
    measured = {
        check_point(point, geometry, "RectangleSketch", tolerance) for point in sketch["points"]
    }
    require(
        len(sketch["points"]) == len(identities) == 4 and measured == identities,
        "four owned corners do not close the measured perimeter",
    )
    return [
        {
            "id": list(identity),
            "start_world_mm": mm(edge["start_world_m"]),
            "end_world_mm": mm(edge["end_world_m"]),
        }
        for identity, edge in sorted(native.items())
    ]


def check_relations(sketch, old_sketch, rectangle, tolerance):
    geometry = rectangle.Profile.Geometry
    expected_axes = Counter(
        (row["type_code"], (row["segment_native_id"],) * 2) for row in geometry["member_relations"]
    )
    relation_rows = sketch["relations"]
    require(
        Counter(row["type"] for row in relation_rows) == {1: 2, 4: 2, 5: 2, 9: 1},
        "principal relation kind roster differs",
    )
    require(len(relation_rows) == len(old_sketch["relations"]), "historical relation count differs")
    axes, distances, incidence = Counter(), Counter(), Counter()
    origin = None
    for fresh, old in zip(relation_rows, old_sketch["relations"], strict=True):
        kind = fresh["type"]
        slots = fresh["entities"]
        definitions = fresh["definition_entities"]
        require(
            kind == old["type"]
            and fresh["entity_types"] == old["entity_types"] == ([3] if kind in (4, 5) else [2, 2])
            and [participant(row) for row in slots] == [participant(row) for row in old["entities"]]
            and len(slots) == len(definitions) == len(fresh["entity_types"]),
            "historical relation operands differ",
        )
        if kind in (4, 5):
            (segment,) = slots
            require(
                slots == definitions
                and segment["kind"] == "sketch_segment"
                and segment["type"] == 0
                and segment["same_sketch"] is True,
                "axis relation lacks an owned segment",
            )
            axes[(kind, participant(segment))] += 1
            continue
        current = [check_point(point, geometry, "RectangleSketch", tolerance) for point in slots]
        incidence.update(current)
        for point, historical in zip(slots, old["entities"], strict=True):
            close_vector(
                mm(point["local_m"]),
                historical["point_local_mm"],
                tolerance,
                "historical relation point differs",
            )
        if kind == 1:
            require(
                slots == definitions, "distance definition operands differ from the current sketch"
            )
            distances[tuple(current)] += 1
            continue
        (coincidence,) = rectangle.Profile.Coincidences
        (proxy,) = geometry["external_point_references"]
        external, corner = definitions
        origin_id = check_point(external, geometry, "Origin", tolerance)
        require(
            not coincidence["deleted"]
            and not coincidence["suppressed"]
            and current == coincidence["point_native_ids"]
            and proxy["local_id"] == current[0]
            and proxy["feature_id"] == rectangle.Origin.FeatureId
            and proxy["handle_class"] == "sgPointHandle"
            and proxy["handle_fields"] == (0, -1, 0)
            and origin_id == (0, 1)
            and corner == slots[1],
            "coincidence definition does not resolve from saved proxy to actual Origin",
        )
        origin = {
            "current_point_ids": current,
            "origin_feature_id": proxy["feature_id"],
            "definition_origin_point_id": origin_id,
            "definition_corner_id": current[1],
        }
    require(axes == expected_axes and origin is not None, "saved axis or Origin relations differ")
    require(
        incidence
        == Counter({row["id"]: row["tally"] for row in geometry["point_relation_tallies"]}),
        "saved sketch point incidence differs",
    )
    return axes, distances, origin


def check_dimensions(sketch, old_feature, geometry, distances, tolerance):
    saved = indexed(geometry["length_dimensions"], lambda row: row["name"])
    old = indexed(old_feature["dimensions"], lambda row: row["name"])
    native = indexed(sketch["dimensions"], lambda row: row["name"])
    require(
        saved.keys() == old.keys() == native.keys() == {"width_mm", "height_mm"},
        "display dimension names differ",
    )
    operands, dimensions = Counter(), {}
    for name, dimension in sorted(native.items()):
        identity = tuple(
            check_point(point, geometry, "RectangleSketch", tolerance)
            for point in dimension["attachments"]
        )
        require(
            dimension["owner"] == sketch["feature"]
            and dimension["same_owner"] is True
            and dimension["dangling"] is False
            and dimension["type"] == 2
            and dimension["attachment_status"] == "observed_slots"
            and dimension["attachment_count"] == 2
            and dimension["attachment_types"] == [11, 11]
            and dimension["driven_state"] == old[name]["driven_state"] == 2
            and dimension["full_name"] == old[name]["full_name"]
            and identity == tuple(saved[name]["point_native_ids"]),
            "direct native dimension role or ordered display attachment differs",
        )
        value = 1000 * dimension["system_value"]
        require(
            all(
                math.isclose(value, 1000 * other, rel_tol=0, abs_tol=tolerance)
                for other in (saved[name]["metres"], old[name]["system_value"])
            ),
            "native dimension value differs",
        )
        operands[identity] += 1
        dimensions[name] = {
            "native_dimension_id": saved[name]["native_id"],
            "value_mm": value,
            "driven_state": dimension["driven_state"],
            "point_ids": identity,
        }
    require(operands == distances, "dimension display targets and distance relations differ")
    return dimensions


def check_body(stage, history, rectangle, historical_edges, tolerance, has_boss_display):
    boss, body = stage["boss"], stage["final_body"]
    require(stage["solid_body_count"] == history["body_count"], "solid body count differs")
    if rectangle.Boss is None:
        require(
            boss is body is None
            and stage["solid_body_count"] == 0
            and history["volume_mm3"] is history["center_of_mass_mm"] is None,
            "sketch-only capture unexpectedly has solid mass or a boss",
        )
        return None, None
    stored = rectangle.Boss
    (historical,) = [row for row in history["feature_tree"] if row["name"] == stored["name"]]
    (historical_dim,) = historical["dimensions"]
    depth = stored["depth_display"]["dimension"]
    end = stored["end_specification"]
    sign = -1 if boss["reverse_direction"] else 1
    require(
        boss["feature"] == feature(stored["name"], "Extrusion", stored["native_feature_id"])
        and boss["profile"] == stage["sketch"]["feature"]
        and stored["profile_object"] == rectangle.Profile.ObjectIndex
        and historical["type"] == "Extrusion"
        and historical["suppressed"] is False
        and {key: boss[key] for key in historical["operation"]} == historical["operation"]
        and boss["end_condition"] == end["conditions"][0] == 0
        and boss["both_directions"] is False
        and end["single_end"] == 1
        and boss["reverse_direction"] is bool(end["direction"])
        and historical_dim["name"] == depth["parameter_name"] == "depth_mm"
        and historical_dim["driven_state"] == 2,
        "boss owner, depth role or signed blind operation differs",
    )
    length = tolerance["length_mm_absolute"]
    depth_mm = 1000 * boss["depth_m"]
    require(
        depth_mm > 0
        and all(
            math.isclose(depth_mm, 1000 * other, rel_tol=0, abs_tol=length)
            for other in (depth["metres"], historical_dim["system_value"])
        ),
        "blind depth differs from its independent historical value",
    )
    require(
        ("depth_dimension" in boss) == has_boss_display,
        "fresh boss display coverage differs from its collector",
    )
    display = boss.get("depth_dimension")
    if has_boss_display:
        require(
            display["owner"] == boss["feature"]
            and display["name"] == historical_dim["name"]
            and display["full_name"] == historical_dim["full_name"]
            and display["driven_state"] == historical_dim["driven_state"]
            and math.isclose(1000 * display["system_value_m"], depth_mm, rel_tol=0, abs_tol=length),
            "fresh boss display name, owner, role or value differs",
        )
    extrusion = [axis * sign * depth_mm for axis in rectangle.Directions[2]]
    points = [edge["start_world_mm"] for edge in historical_edges]
    extents = list(
        zip(
            *(
                points
                + [[a + b for a, b in zip(point, extrusion, strict=True)] for point in points]
            ),
            strict=True,
        )
    )
    minimum, maximum = mm(body["bounds_min_m"]), mm(body["bounds_max_m"])
    close_vector(
        minimum,
        [min(axis) for axis in extents],
        length,
        "body minimum differs from the signed profile extent",
    )
    close_vector(
        maximum,
        [max(axis) for axis in extents],
        length,
        "body maximum differs from the signed profile extent",
    )
    topology = [body[f"{item}_count"] for item in ("face", "edge", "vertex")]
    require(
        body["solid_body_count"] == stage["solid_body_count"] == 1 and topology == [6, 12, 8],
        "fresh body does not have the observed rectangular prism topology",
    )
    volume = 1e9 * body["volume_m3"]
    centroid = mm(body["center_of_mass_m"])
    require(
        math.isclose(
            volume,
            history["volume_mm3"],
            rel_tol=tolerance["volume_relative"],
            abs_tol=tolerance["volume_mm3_absolute"],
        ),
        "solid volume differs from historical reopen",
    )
    close_vector(
        centroid,
        history["center_of_mass_mm"],
        length,
        "solid centroid differs from historical reopen",
    )
    return (
        {
            "feature_id": stored["native_feature_id"],
            "profile_id": rectangle.Profile.FeatureId,
            "depth_mm": depth_mm,
            "direction_multiplier": sign,
            "signed_extent_world_mm": extrusion,
            "end_condition": boss["end_condition"],
            "historical_depth_dimension": {
                "native_dimension_id": depth["native_dimension_id"],
                "driven_state": historical_dim["driven_state"],
            },
            "fresh_depth_dimension": (
                None
                if display is None
                else {
                    "name": display["name"],
                    "value_mm": 1000 * display["system_value_m"],
                    "driven_state": display["driven_state"],
                    "owner_feature_id": display["owner"]["id"],
                }
            ),
        },
        {
            "topology_faces_edges_vertices": topology,
            "bounds_min_mm": minimum,
            "bounds_max_mm": maximum,
            "volume_mm3": volume,
            "center_of_mass_mm": centroid,
        },
    )


def compare_stage(stage, history, rectangle, tolerances, has_boss_display):
    sketch = stage["sketch"]
    (old_sketch,) = [
        row for row in history["sketches"] if row["name"] == rectangle.Profile.NameValue
    ]
    (old_feature,) = [
        row for row in history["feature_tree"] if row["name"] == rectangle.Profile.NameValue
    ]
    support = stage["support"]
    require(
        stage["configuration"] == history["configuration"] == "Default"
        and stage["units_code"] == history["units_code"]
        and stage["support_type"] == old_sketch["support_type"] == 4
        and support
        == feature(old_sketch["support_name"], "RefPlane", rectangle.Reference.FeatureId)
        and support["name"] == rectangle.Datum.NameValue
        and stage["region_count"] == old_sketch["region_count"] == 1
        and stage["constraint_status"] == old_sketch["constraint_status"] == 3
        and old_sketch["fully_defined"] is True
        and sketch["feature"]
        == feature(rectangle.Profile.NameValue, "ProfileFeature", rectangle.Profile.FeatureId)
        and stage["origin_feature"]
        == feature(rectangle.Origin.NameValue, "OriginProfileFeature", rectangle.Origin.FeatureId),
        "saved sketch support, units, region, feature or constraint state differs",
    )
    transform = sketch["model_to_sketch_transform"]
    expected = (*(rectangle.Reference.BasisValue or KUnitRows), *rectangle.Reference.ShiftScale)
    require(
        transform == old_sketch["model_to_sketch_transform"]
        and tuple(transform[:13]) == expected
        and rectangle.Reference.ShiftScale == (0, 0, 0, 1),
        "saved and measured principal frames differ",
    )
    length = tolerances["length_mm_absolute"]
    perimeter = check_perimeter(stage, old_sketch, rectangle, length)
    axes, distances, origin = check_relations(sketch, old_sketch, rectangle, length)
    dimensions = check_dimensions(
        sketch, old_feature, rectangle.Profile.Geometry, distances, length
    )
    operation, body = check_body(
        stage, history, rectangle, old_sketch["entities"], tolerances, has_boss_display
    )
    return {
        "configuration": stage["configuration"],
        "units_code": stage["units_code"],
        "support": support,
        "profile_feature_id": rectangle.Profile.FeatureId,
        "model_to_sketch_transform": transform,
        "constraint_status": stage["constraint_status"],
        "region_count": stage["region_count"],
        "perimeter": perimeter,
        "axis_relations": [
            {"type": kind, "segment_id": identity} for kind, identity in sorted(axes.elements())
        ],
        "origin_coincidence": origin,
        "dimensions": dimensions,
        "boss": operation,
        "body": body,
        "solid_body_count": stage["solid_body_count"],
        "source_counts": {
            "archive_sketch_value_dimensions": len(rectangle.Profile.Geometry["length_dimensions"]),
            "archive_boss_value_dimensions": int(operation is not None),
            "archive_axis_relations": len(rectangle.Profile.Geometry["member_relations"]),
            "archive_point_coincidences": len(rectangle.Profile.Coincidences),
            "fresh_sketch_display_dimensions": len(sketch["dimensions"]),
            "fresh_boss_display_dimensions": int(operation is not None and has_boss_display),
            "fresh_display_attachment_slots": sum(
                len(row["attachments"]) for row in sketch["dimensions"]
            ),
            "fresh_current_relations": len(sketch["relations"]),
            "fresh_current_relation_slots": sum(
                len(row["entities"]) for row in sketch["relations"]
            ),
            "fresh_definition_relation_slots": sum(
                len(row["definition_entities"]) for row in sketch["relations"]
            ),
        },
    }


def report(directory, digest):
    snapshot = GitSnapshot(ROOT)
    dispatch, plan, run, digests = read_dispatch(directory, digest)
    verify_owner(run, dispatch)
    sources, installed = read_sources(snapshot, plan)
    has_boss_display, _ = COLLECTORS[sources["collector"]["sha256"]]
    specs = snapshot.document(CAPTURE_REVISION, SPEC)
    require(
        sha256(snapshot.blob(CAPTURE_REVISION, SPEC)) == SPEC_DIGEST,
        "historical specification digest mismatch",
    )
    native_files, captures, historical_controls = read_captures(snapshot, plan, specs)
    tolerance = specs["comparison_tolerances"]
    before, after = run["control_before"], run["control_after"]
    for control in (before, after):
        require(
            control["file"] == "control.SLDPRT"
            and control["status"] == "observed"
            and control["open"] == CLEAN_OPEN
            and control["body_count"] == 1,
            "fresh healthy control failed",
        )
    require(
        math.isclose(
            before["volume_mm3"],
            after["volume_mm3"],
            rel_tol=tolerance["volume_relative"],
            abs_tol=tolerance["volume_mm3_absolute"],
        ),
        "fresh healthy control volumes differ",
    )
    close_vector(
        mm(before["center_of_mass_m"]),
        mm(after["center_of_mass_m"]),
        tolerance["length_mm_absolute"],
        "fresh healthy control centers differ",
    )
    for prior in historical_controls:
        require(
            prior["native_sha256"] == CONTROL_DIGEST
            and prior["body_count"] == before["body_count"]
            and math.isclose(
                prior["volume_mm3"],
                before["volume_mm3"],
                rel_tol=tolerance["volume_relative"],
                abs_tol=tolerance["volume_mm3_absolute"],
            ),
            "fresh and historical healthy controls disagree",
        )
        close_vector(
            mm(before["center_of_mass_m"]),
            prior["center_of_mass_mm"],
            tolerance["length_mm_absolute"],
            "fresh and historical healthy control centers differ",
        )
    observations = indexed(run["observations"], lambda row: row["file"])
    require(
        observations.keys() == native_files.keys(),
        "fresh observation roster differs from pinned saves",
    )
    cases, totals = [], Counter()
    for name, (family, variant, pin, history) in sorted(native_files.items()):
        observation = observations[name]
        try:
            require(
                observation["status"] == "observed"
                and observation["open"] == CLEAN_OPEN
                and history["open_status"] == {"errors": 0, "warnings": 0},
                "unclean open",
            )
            require(
                observation[PHASES[0]] == observation[PHASES[1]],
                "native rebuild changed an observed field",
            )
            archive = SldprtArchive.from_bytes(snapshot.blob(CAPTURE_REVISION, pin["path"]), name)
            require(ContainerMo(archive.streams) == 19000, "unsupported model generation")
            rectangle = ReadRectPart(
                archive.require("Contents/Config-0"),
                archive.require("Contents/Config-0-ResolvedFeatures"),
                19000,
            )
            require(
                (rectangle.Boss is not None) == (family == "P03"),
                "typed boss ownership differs by family",
            )
            phases = {}
            for phase in PHASES:
                try:
                    phases[phase] = compare_stage(
                        observation[phase], history, rectangle, tolerance, has_boss_display
                    )
                except (LookupError, ValueError) as error:
                    raise ValueError(f"{phase}: {error}") from error
                result = phases[phase]
                totals.update(result["source_counts"])
                totals.update(
                    {
                        "perimeter_edges": len(result["perimeter"]),
                        "axis_relations": len(result["axis_relations"]),
                        "origin_coincidences": 1,
                        "boss_operations": int(result["boss"] is not None),
                    }
                )
        except (ArchiveError, LookupError, ValueError) as error:
            raise ValueError(f"{name}: {error}") from error
        cases.append({"capture": family, "variant": variant, "file": name, "native": pin, **phases})
    return {
        "schema": 1,
        "claim": "licensed_same_format_discovery_comparison",
        "qualification": False,
        "source_revision": plan["source_revision"],
        "original_capture_revision": CAPTURE_REVISION,
        "dispatch_sha256": digest,
        "readback_sha256": digests,
        "source_pins": sources,
        "installed_file_sha256": installed,
        "historical_captures": captures,
        "solidworks_build": BUILD,
        "native_owner_sha256": dispatch["proof"]["native_owner_sha256"],
        "owned_process_exit_observed": True,
        "healthy_control_volume_mm3": before["volume_mm3"],
        "unchanged_rebuilds": len(cases),
        "phase_counts": dict(totals),
        "cases": cases,
    }


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("copied_output", type=Path)
    parser.add_argument("--dispatch-sha256", required=True)
    args = parser.parse_args()
    try:
        value = report(args.copied_output, args.dispatch_sha256)
    except (LookupError, OSError, TypeError, ValueError) as error:
        parser.exit(1, f"principal readback refused: {error}\n")
    sys.stdout.buffer.write(
        (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()
    )


if __name__ == "__main__":
    main()
