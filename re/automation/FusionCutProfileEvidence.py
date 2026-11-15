import json
import math

from FusionBossProfileEvidence import selected_profile
from FusionCutExtentEvidence import (
    REVISION,
    design_members,
    inspect_archive,
    p04_capture,
    record_site,
)
from FusionCutFaceEvidence import body_members, inspect_face
from FusionCutJournalEvidence import feature_clocks, kernel_actor_join
from FusionCutSketchEvidence import historical_observations, inspect_sketches
from PairedCaptureIntake import require, sha256

from decode_basics import named_features, sketch_references
from decode_profiles import PROFILE_LOOP_GUID, decode_profiles
from decode_sketch import reference, same
from fusion_metadata import design_records


# membership precedes area so a coincident region size cannot choose the selected loop
def rectangle_area(lines):
    require(len(lines) == 4, "P04 selected rectangle does not have four lines")
    endpoints = []
    point_ids = set()
    for line in lines:
        require(
            line["kind"] == "Line" and line["start_cm"][2] == line["end_cm"][2] == 0,
            "P04 rectangle endpoints do not lie in the saved sketch plane",
        )
        endpoints.extend((line["start_cm"][:2], line["end_cm"][:2]))
        point_ids.update((line["start_point_id"], line["end_point_id"]))
    axis_limits = [(min(axis), max(axis)) for axis in zip(*endpoints, strict=True)]
    widths = [maximum - minimum for minimum, maximum in axis_limits]
    require(
        len(point_ids) == 4 and min(widths) > 2e-9,
        "P04 rectangle corners are ambiguous",
    )
    corners = []
    for point in endpoints:
        corner = []
        for value, limits in zip(point, axis_limits, strict=True):
            (choice,) = [
                side
                for side, limit in enumerate(limits)
                if math.isclose(value, limit, abs_tol=1e-9, rel_tol=0)
            ]
            corner.append(choice)
        corners.append(tuple(corner))
    edges = {
        frozenset((start, end))
        for start, end in zip(corners[::2], corners[1::2], strict=True)
    }
    expected = {frozenset(((0, side), (1, side))) for side in (0, 1)} | {
        frozenset(((side, 0), (side, 1))) for side in (0, 1)
    }
    require(edges == expected, "P04 line set is not the authored rectangle perimeter")
    return {
        "bounds_cm": [list(pair) for pair in zip(*axis_limits, strict=True)],
        "area_mm2": 100 * math.prod(widths),
    }


# the verified cut descriptor names the sketch before its loop records are decoded
def selected_cut_profile(data, records, feature, sketch, routes):
    features = [feature, sketch]
    sketch_references(data, records, features)
    (source,) = feature["sketch_reference_candidates"]
    descriptor = routes["cut_profile_descriptor"]
    require(
        source["reference_record_offset"] == descriptor["record_offset"]
        and source["feature_object_id"]
        == routes["cut_sketch_feature"]["object_id"]
        == sketch["object_id"]
        and source["sketch_object_id"]
        == routes["cut_sketch_data"]["object_id"]
        == sketch["sketch_object_id"],
        "P04 cut profile names another sketch",
    )
    decoded = decode_profiles(data, records, features)
    require(
        len(decoded["decoded"]) == 1 and not decoded["unresolved"],
        "P04 cut profile loop unresolved",
    )
    (selection,) = feature["profile_selection"]
    (definition,) = [
        r
        for r in records
        if r.is_primary and r.object_id == selection["loop_definition_object_id"]
    ]
    require(
        definition.class_guid == PROFILE_LOOP_GUID
        and selection["descriptor_object_id"] == descriptor["object_id"]
        and reference(data, definition.body + 2) == descriptor["object_id"],
        "P04 cut loop owner or type differs",
    )
    return {
        "profile_proxy": routes["cut_profile_proxy"],
        "profile_descriptor": descriptor,
        "profile_loop_definition": record_site(data, definition),
        "selection": selection,
    }


# the archived api flags distinguish authored profile edges from reference and construction lines
def profile_region(selection, geometry, observed, *, cut):
    (loop,) = selection["loops"]
    members = [row["entity_id"] for row in loop["curve_references"]]
    require(
        loop["is_outer"]
        and len(members) == len(set(members)) == 4
        and all(row["entity_kind"] == "Line" for row in loop["curve_references"]),
        "P04 profile lacks one unique four-line outer loop",
    )
    history = {row["index"]: row for row in observed["curves"]}
    lines = [row for row in geometry if row["kind"] == "Line"]
    roles = {"authored": [], "reference": [], "construction": []}
    for line in lines:
        prior = history[line["historical_curve_index"]]
        require(
            not (prior["reference"] and prior["construction"]),
            "P04 reference and construction line roles overlap",
        )
        role = (
            "reference"
            if prior["reference"]
            else "construction" if prior["construction"] else "authored"
        )
        roles[role].append(line)
    require(
        {line["object_id"] for line in roles["authored"]} == set(members),
        "P04 selected profile does not exhaust the independently measured authored perimeter",
    )
    region = rectangle_area(roles["authored"])
    areas = [region["area_mm2"]]
    excluded = {}
    if cut:
        (diagonal,) = roles["construction"]
        outer = rectangle_area(roles["reference"])
        lower, upper = region["bounds_cm"]
        outer_lower, outer_upper = outer["bounds_cm"]
        require(
            all(
                a < b < c < d
                for a, b, c, d in zip(
                    outer_lower, lower, upper, outer_upper, strict=True
                )
            ),
            "P04 selected rectangle is not within the projected reference boundary",
        )
        ends = [diagonal["start_cm"][:2], diagonal["end_cm"][:2]]
        member_points = {
            line[key]
            for line in roles["authored"]
            for key in ("start_point_id", "end_point_id")
        }
        require(
            {diagonal["start_point_id"], diagonal["end_point_id"]} <= member_points
            and all(
                all(
                    any(
                        math.isclose(value, limit, abs_tol=1e-9, rel_tol=0)
                        for limit in (low, high)
                    )
                    for value, low, high in zip(end, lower, upper, strict=True)
                )
                for end in ends
            )
            and all(
                not math.isclose(a, b, abs_tol=1e-9, rel_tol=0)
                for a, b in zip(*ends, strict=True)
            ),
            "P04 excluded construction line is not the measured diagonal",
        )
        areas.append(outer["area_mm2"] - areas[0])
        excluded = {
            "reference_line_object_ids": [
                row["object_id"] for row in roles["reference"]
            ],
            "construction_diagonal_object_id": diagonal["object_id"],
            "reference_rectangle": outer,
        }
    else:
        require(
            not roles["reference"] and not roles["construction"],
            "P04 boss rectangle has unexpected excluded lines",
        )
    require(
        same(sorted(areas), sorted(observed["profile_areas_mm2"]))
        and all(region["area_mm2"] < area for area in areas[1:]),
        "P04 selected and independently measured profile areas disagree",
    )
    return {
        "stored_member_object_ids": members,
        "selected_rectangle": region,
        "excluded_lines": excluded,
        "historically_measured_profile_areas_mm2": observed["profile_areas_mm2"],
        "corroborated_region_areas_mm2": areas,
    }


# journal actor clocks and feature selection records provide independent identity anchors
def inspect_profiles(content, observed):
    streams, member_evidence = design_members(content)
    data = streams["BulkStream.dat"]
    records, _ = design_records(data, streams["MetaStream.dat"])
    features = named_features(data, records)
    by_id = {row["object_id"]: row for row in features}
    native = feature_clocks(data, records, observed)
    face = inspect_face(content, observed)
    member = face["native_body_mapping"]["history_blob_member"]
    journal = kernel_actor_join(body_members(content)[member], face, native)
    extent = inspect_archive(content)
    routes = extent["selection_routes"]
    sketches = inspect_sketches(content, observed)["sketches"]
    sketch_by_id = {row["feature_record"]["object_id"]: row for row in sketches}
    observed_by_name = {row["name"]: row for row in observed["sketches"]}

    profiles = {}
    for side, (label, operation) in enumerate((("zero", "NewBody"), ("one", "Cut"))):
        endpoint = journal[f"slot_zero_side_{label}"]
        actor = endpoint["actor"]
        is_cut = operation == "Cut"
        feature = by_id[actor["object_id"]]
        require(
            extent["extrusions"][operation]["record"]["object_id"]
            == feature["object_id"],
            "P04 terminal journal clock actor differs from the saved operation",
        )
        position = actor["timeline_index"]
        require(position > 0, "P04 profile actor lacks its preceding sketch")
        predecessor = native["sequence"]["visible_entries"][position - 1]
        saved = sketch_by_id[predecessor["object_id"]]
        source = by_id[predecessor["object_id"]]
        require(
            source["kind"] == "Sketch", "P04 terminal predecessor is not a typed sketch"
        )
        source["geometry"] = saved["geometry"]
        if is_cut:
            profile = selected_cut_profile(data, records, feature, source, routes)
        else:
            require(
                routes["historical_body_producer"]["object_id"] == feature["object_id"],
                "P04 boss profile actor differs from the historical body producer",
            )
            profile = selected_profile(
                data, records, [source, feature], source, feature
            )
        region = profile_region(
            profile["selection"],
            saved["geometry"],
            observed_by_name[source["name"]],
            cut=is_cut,
        )
        profiles[operation] = {
            "journal_slot": 0,
            "journal_pointer_side": side,
            "journal_endpoint_actor": actor,
            "journal_endpoint_timestamp": endpoint["timestamp"],
            "source_sketch": saved["sketch_record"],
            "profile": profile,
            "region": region,
        }
    return {
        "design_members": member_evidence,
        "asm_history_member": {"path": member, **face["brep_members"][member]},
        "profiles": profiles,
    }


# the paired receipt pins both the source archives and their independent historic measurements
def report():
    git, capture = p04_capture()
    measurement = capture["measurements"]
    content = git.blob(REVISION, measurement["path"])
    require(sha256(content) == measurement["sha256"], "P04 measurement digest differs")
    historical = historical_observations(
        capture, git.parse_document(content, measurement["path"])
    )
    archives = []
    for source in capture["native_files"]:
        phase, observed = historical[source["variant"]]
        archives.append(
            {
                "source": source,
                "historical_phase": phase,
                **inspect_profiles(git.blob(REVISION, source["path"]), observed),
            }
        )
    return {
        "evidence_version": 1,
        "source_revision": REVISION,
        "recipe_id": capture["recipe_id"],
        "split": capture["split"],
        "application_build": capture["application_build"],
        "receipt": capture["receipt"],
        "measurements": measurement,
        "archives": archives,
        "scope": "Saved profile membership and measured region areas joined to journal endpoint actors; fresh profile getters and editable acceptance remain open",
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2, sort_keys=True, allow_nan=False))
