"""Owned ordered Line/Arc and fitted-spline Loft guide source identities.

Descriptor order is explicit. Path traversal/opposed flags and chain-discovery
options remain unresolved; analytic samples describe each natural source curve.
"""

import argparse
import copy
import json
import math
from pathlib import Path
import struct

from decode_loft_modes import decode_loft_modes
from decode_nurbs import evaluate_nurbs, evaluate_nurbs_derivative
from decode_placement import cross, rigid_matrix, transform_point, transform_vector
from decode_selection import native_proxy_references
from decode_sketch import reference, same


# share range safe homogeneous derivatives across loft and sweep source evaluators
def _nurbs_derivative(shape, parameter):
    """Exact homogeneous B-spline derivative, with rational quotient rule."""
    return evaluate_nurbs_derivative(shape, parameter)


# native placement preserves component coordinates without assigning guide traversal semantics
def _source_geometry(sketch, curve):
    if "placement" not in sketch:
        raise ValueError("Composite Loft guide sketch placement unresolved")
    matrix = rigid_matrix(sketch["placement"]["sketch_to_component_matrix"])
    start, end = (transform_point(matrix, curve[key]) for key in ("start_cm", "end_cm"))
    kind = curve["kind"]
    result = {"kind": kind, "start_cm": start, "end_cm": end}
    if kind == "Line":
        low, high = 0.0, 1.0
        delta = [b - a for a, b in zip(start, end)]
        result["length_cm"] = math.sqrt(sum(x * x for x in delta))
        if result["length_cm"] <= 1e-12:
            raise ValueError("Degenerate composite Loft line")

        # exact line coefficients preserve natural source derivatives without sampled approximations
        def evaluate(parameter):
            return [a + parameter * d for a, d in zip(start, delta)], delta

    elif kind == "Arc":
        center = transform_point(matrix, curve["center_cm"])
        normal, axis = (
            transform_vector(matrix, curve[key]) for key in ("normal", "reference_axis")
        )
        radius = curve["radius_cm"]
        low, high = curve["start_angle_radians"], curve["end_angle_radians"]
        if (
            not all(math.isfinite(x) for x in (radius, low, high))
            or radius <= 0
            or not 0 < high - low < 2 * math.pi
            or not same(
                [
                    sum(x * x for x in normal),
                    sum(x * x for x in axis),
                    sum(a * b for a, b in zip(axis, normal)),
                ],
                [1, 1, 0],
            )
        ):
            raise ValueError("Invalid composite Loft natural arc parameters")
        transverse = cross(normal, axis)
        result.update(
            center_cm=center,
            normal=normal,
            reference_axis=axis,
            radius_cm=radius,
            start_angle_radians=low,
            end_angle_radians=high,
            length_cm=radius * (high - low),
        )

        # exact circular coefficients preserve natural source parameters without inferred path reversal
        def evaluate(parameter):
            return (
                [
                    c + radius * (math.cos(parameter) * a + math.sin(parameter) * b)
                    for c, a, b in zip(center, axis, transverse)
                ],
                [
                    radius * (-math.sin(parameter) * a + math.cos(parameter) * b)
                    for a, b in zip(axis, transverse)
                ],
            )

    elif kind == "FittedSpline":
        shape = copy.deepcopy(curve["nurbs"])
        if shape["is_periodic"] or same(start, end):
            raise ValueError("Periodic or closed spline Loft guide remains unverified")
        shape["control_points_cm"] = [
            transform_point(matrix, point) for point in shape["control_points_cm"]
        ]
        shape["representation"] = (
            "Stored NURBS controls transformed into parent component coordinates"
        )
        low, high = shape["parameter_domain"]
        result.update(
            nurbs=shape,
            length_status="Not evaluated; no sampled-polyline length substituted for the API getter",
        )

        # shared rational arithmetic preserves natural spline positions and first derivatives
        def evaluate(parameter):
            return evaluate_nurbs(shape, parameter), _nurbs_derivative(shape, parameter)

    else:
        raise ValueError("Unsupported composite Loft source curve class")
    samples = []
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        parameter = low + fraction * (high - low)
        position, derivative = evaluate(parameter)
        samples.append(
            {
                "parameter_fraction": fraction,
                "parameter": parameter,
                "point_component_cm": position,
                "parameter_derivative_component": derivative,
            }
        )
    if not same(start, samples[0]["point_component_cm"]) or not same(
        end, samples[-1]["point_component_cm"]
    ):
        raise ValueError(
            "Composite Loft source endpoints disagree with analytic geometry"
        )
    result.update(
        parameter_domain=[low, high],
        analytic_samples=samples,
        coordinate_scope="Natural source curve in parent component coordinates; occurrence/joint transforms not applied",
    )
    return result


# owned descriptors preserve explicit guide membership before coordinates are evaluated
def resolve_loft_composite_guide(data, records, selection_id, owner_id, features):
    """Five-argument guide_resolver for observed same-sketch Line/Arc or spline."""
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {key: values[0] for key, values in grouped.items() if len(values) == 1}

    # typed ownership prevents guide selections from borrowing unrelated geometry records
    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError(
                "Composite Loft guide typed identity missing, ambiguous or wrong class"
            )
        return record, data[record.body : record.end]

    proxy, payload = typed(selection_id, "2CA5A1CD-C99B-4C9B-91AF-57989148E841")
    descriptors, props = native_proxy_references(data, proxy)
    if (
        props
        or len(descriptors) not in (1, 2)
        or len(set(descriptors)) != len(descriptors)
        or reference(payload, len(payload) - 11) != owner_id
    ):
        raise ValueError("Unobserved composite Loft proxy count/attributes/owner")
    secondary = 6 + 11 * len(descriptors)
    if payload[:2] != b"\0\0" or payload[secondary : secondary + 6] != b"\0\0\1\0\0\0":
        raise ValueError("Unobserved composite Loft secondary list")
    flags_id = reference(payload, secondary + 6)
    _, flags = typed(flags_id, "2DF7DA30-A4E4-4260-AFD1-D9C7154CB44B")
    if flags != bytes.fromhex("0000010100"):
        raise ValueError("Unobserved composite Loft secondary flags")
    members = []
    class_guids = {
        "Line": "DCA267ED-D615-4934-B64F-AD805E8003E2",
        "Arc": "F0130424-8B7E-4092-93C9-1CA807482534",
        "FittedSpline": "D82E012F-6DDD-4AED-BDE1-C0F7F9100B9B",
    }
    for index, identity in enumerate(descriptors):
        _, descriptor = typed(identity, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
        if (
            len(descriptor) != 263
            or descriptor[:2] != b"\0\0"
            or struct.unpack_from("<I", descriptor, 13)[0] != 1
            or reference(descriptor, 252) != owner_id
        ):
            raise ValueError("Composite Loft descriptor count/layout/owner mismatch")
        leaf_id = reference(descriptor, 2)
        _, leaf = typed(leaf_id, "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8")
        if len(leaf) != 26 or leaf[:10] != b"\0" * 10:
            raise ValueError("Unsupported composite Loft sketch-curve leaf")
        sketch_id, tag = struct.unpack_from("<QQ", leaf, 10)
        sketches = [
            f
            for f in features
            if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id
        ]
        matches = [
            (sketch, curve)
            for sketch in sketches
            for curve in sketch.get("geometry", [])
            if curve.get("entity_tag") == tag and curve["kind"] in class_guids
        ]
        if len(sketches) != 1 or len(matches) != 1:
            raise ValueError(
                "Composite Loft source sketch/tag missing, unsupported or ambiguous"
            )
        sketch, curve = matches[0]
        typed(curve["object_id"], class_guids[curve["kind"]])
        members.append(
            {
                "index": index,
                "descriptor_object_id": identity,
                "terminal_object_id": leaf_id,
                "sketch_object_id": sketch_id,
                "sketch_name": sketch.get("name"),
                "curve_object_id": curve["object_id"],
                "curve_entity_tag": tag,
                "kind": curve["kind"],
                "natural_component_geometry": _source_geometry(sketch, curve),
                "path_is_opposed_to_entity": None,
            }
        )
    if len({m["sketch_object_id"] for m in members}) != 1:
        raise ValueError("Cross-sketch composite Loft guides remain unverified")
    kinds = [m["kind"] for m in members]
    if kinds == ["Line", "Arc"]:
        line, arc = [m["natural_component_geometry"] for m in members]
        if not same(line["end_cm"], arc["end_cm"]) or same(
            line["start_cm"], arc["start_cm"]
        ):
            raise ValueError("Unobserved composite Loft endpoint connection")
        one = line["analytic_samples"][-1]["parameter_derivative_component"]
        two = arc["analytic_samples"][-1]["parameter_derivative_component"]
        lengths = [math.sqrt(sum(x * x for x in vector)) for vector in (one, two)]
        if not same([x / lengths[0] for x in one], [-x / lengths[1] for x in two]):
            raise ValueError("Unobserved nontangent Line/Arc Loft guide")
        kind = "CompositeSketchGuide"
    elif kinds == ["FittedSpline"]:
        kind = "FittedSplineGuide"
    else:
        raise ValueError(
            "Only observed ordered Line/Arc or single FittedSpline guides supported"
        )
    return {
        "kind": kind,
        "selection_record_object_id": selection_id,
        "sketch_object_id": members[0]["sketch_object_id"],
        "sketch_name": members[0]["sketch_name"],
        "member_count": len(members),
        "members": members,
        "secondary_flags_record_object_id": flags_id,
        "secondary_flags_hex": flags.hex(),
        "order_scope": "Explicit counted native descriptor order; observed API member order agrees in captured Line/Arc paths",
        "traversal_scope": "Source natural geometry only; Path member traversal/opposed flags are unresolved and not inferred from endpoint connectivity",
        "chain_option_scope": "Invariant secondary flags retained without chain-option semantics; connected discovery and explicit member input produce the same observed layout",
        "coordinate_scope": "Parent component coordinates; no occurrence/joint transformations or Loft regeneration",
    }


# qualified callbacks preserve existing loft controls while admitting explicit composite guides
def decode_loft_composite_guides(data, records, body, feature, features):
    result = decode_loft_modes(
        data,
        records,
        body,
        feature,
        features,
        guide_resolver=resolve_loft_composite_guide,
    )
    if (
        result["operation"] != "NewBody"
        or result["is_closed"]
        or not result["is_solid"]
        or result["section_count"] != 2
        or result["guide_count"] != 1
        or any("profile" not in section for section in result["sections"])
        or any(
            (result.get(side + "_condition") or {}).get("type") != "Free"
            for side in ("start", "end")
        )
    ):
        raise ValueError(
            "Composite Loft wrapper requires open solid two-profile NewBody, Free ends and exactly one guide"
        )
    if result["is_centerline"]:
        selected = result["centerline"]
        if result["rails"]:
            raise ValueError("Combined composite Loft guide kinds remain unverified")
    else:
        if result["centerline"] is not None or len(result["rails"]) != 1:
            raise ValueError(
                "Composite Loft requires one rail when no centerline is present"
            )
        selected = result["rails"][0]["selection"]
        if selected["kind"] != "CompositeSketchGuide":
            raise ValueError("Spline Loft rail remains unverified")
    cursor = result["result_anchor_list_end_relative_offset"]
    if (
        body[cursor : cursor + 8] != b"\0" * 8
        or struct.unpack_from("<I", body, cursor + 8)[0] != 36
    ):
        raise ValueError("Unobserved composite Loft post-anchor list framing")
    result["guide_status"] = (
        "Owned same-sketch ordered tangent Line/Arc centerline/rail, or single fitted-spline centerline; natural geometry decoded, traversal/opposition unresolved"
    )
    return result


# saved native and api evidence distinguish verified guide behavior from unsupported combinations
def validate_fixtures(root, zstd_library):
    from decode_basics import decode_basics
    from fusion_archive import read_members
    from fusion_metadata import design_records

    folder = root / "loftcompositeguides-8ea2ef593872"
    truth = json.loads((folder / "ground_truth.json").read_text())
    assert (
        (folder / "complete.txt").is_file()
        and not truth["errors"]
        and len(truth["samples"]) == 4
    )
    report = {
        "api_version": truth["fusion_version"],
        "samples": [],
        "negative_checks": [],
        "interface": "decode_loft_composite_guides(data,records,body,feature,features); resolve_loft_composite_guide is the existing five-argument guide_resolver hook",
        "validation_command": "python3 decode_loft_composite_guides.py --validate --zstd-library <local libzstd path>",
    }
    for sample in truth["samples"]:
        assert not sample["getter_errors"]
        archive = folder / sample["file"]
        main = decode_basics(archive, zstd_library)
        stream = next(
            s
            for s in main["streams"]
            if any(f["kind"] == "Loft" for f in s["features"])
        )
        features = stream["features"]
        feature = next(f for f in features if f["kind"] == "Loft")
        members = read_members(archive, zstd_library)
        data = members[stream["member"]]
        records, _ = design_records(
            data,
            members.get(stream["member"].replace("BulkStream.dat", "MetaStream.dat")),
        )
        record = next(
            r for r in records if r.is_primary and r.object_id == feature["object_id"]
        )
        settings = decode_loft_composite_guides(
            data, records, data[record.body : record.end], feature, features
        )
        selected = (
            settings["centerline"]
            if settings["is_centerline"]
            else settings["rails"][0]["selection"]
        )
        api_guide = sample["settings"]["guides"][0]
        api_sources = (
            [m["source"] for m in api_guide["path"]["members"]]
            if api_guide["path"]
            else [api_guide["curve"]]
        )
        checks = {
            "native_order_matches_actual_api_source_member_kinds": [
                m["kind"] for m in selected["members"]
            ]
            == [
                m["entity_type"].split("::")[-1].removeprefix("Sketch")
                for m in api_sources
            ],
            "controls_match_actual_api": all(
                settings[k] == sample["settings"][k]
                for k in (
                    "is_solid",
                    "is_closed",
                    "is_tangent_edges_merged",
                    "section_count",
                    "guide_count",
                    "is_centerline",
                )
            ),
            "opposed_flags_remain_unresolved_in_decoded_output": all(
                m["path_is_opposed_to_entity"] is None for m in selected["members"]
            ),
        }
        for member, actual in zip(selected["members"], api_sources):
            natural, actual_geometry = (
                member["natural_component_geometry"],
                actual["natural_world_geometry"],
            )
            prefix = member["kind"] + "_"
            checks[prefix + "parameter_domain_matches_actual_source"] = same(
                natural["parameter_domain"], actual_geometry["parameter_extents"]
            )
            checks[prefix + "five_natural_source_points_match_actual_api"] = all(
                same(a["point_component_cm"], b["point_cm"])
                for a, b in zip(natural["analytic_samples"], actual_geometry["samples"])
            )
            checks[prefix + "five_parameter_derivatives_match_actual_getTangent"] = all(
                same(a["parameter_derivative_component"], b["tangent"])
                for a, b in zip(natural["analytic_samples"], actual_geometry["samples"])
            )
            if member["kind"] == "FittedSpline":
                source, actual_nurbs = natural["nurbs"], actual_geometry["nurbs"]
                checks[
                    "stored_nurbs_degree_knots_weights_controls_match_actual_api"
                ] = (
                    source["degree"] == actual_nurbs["degree"]
                    and source["is_rational"] == actual_nurbs["is_rational"]
                    and source["is_periodic"] == actual_nurbs["is_periodic"]
                    and same(source["knots"], actual_nurbs["knots"])
                    and same(source["weights"], actual_nurbs["weights"])
                    and len(source["control_points_cm"])
                    == len(actual_nurbs["control_points_cm"])
                    and all(
                        same(a, b)
                        for a, b in zip(
                            source["control_points_cm"],
                            actual_nurbs["control_points_cm"],
                        )
                    )
                )
        assert all(checks.values()), (sample["file"], checks)
        report["samples"].append(
            {
                "archive": str(archive.relative_to(root)),
                "checks": checks,
                "decoded": settings,
                "actual_api_guide": api_guide,
                "actual_input_path": sample["input_path_before_loft"],
                "requested_path_mode": sample["requested_path_mode"],
                "api_evidence_scope": "Actual Path order/opposed flags and oriented geometry retained as evidence only; decoded samples describe natural source geometry",
            }
        )
        if selected["kind"] == "CompositeSketchGuide":
            baseline = data, records, features, feature, selected
    data, records, features, feature, selected = baseline
    first = selected["members"][0]
    for label, identity, delta, value in (
        (
            "Descriptor owner mismatch",
            first["descriptor_object_id"],
            253,
            struct.pack("<Q", selected["sketch_object_id"]),
        ),
        (
            "Curve leaf tag missing",
            first["terminal_object_id"],
            18,
            struct.pack("<Q", 999999),
        ),
        (
            "Unobserved secondary flags",
            selected["secondary_flags_record_object_id"],
            2,
            b"\0",
        ),
    ):
        record = next(r for r in records if r.is_primary and r.object_id == identity)
        corrupted = bytearray(data)
        corrupted[record.body + delta : record.body + delta + len(value)] = value
        try:
            resolve_loft_composite_guide(
                bytes(corrupted),
                records,
                selected["selection_record_object_id"],
                feature["object_id"],
                features,
            )
        except ValueError as error:
            report["negative_checks"].append(
                {"check": label, "passed": True, "reason": str(error)}
            )
        else:
            raise AssertionError(label)
    altered = copy.deepcopy(features)
    sketch = next(
        f
        for f in altered
        if f["kind"] == "Sketch"
        and f["sketch_object_id"] == selected["sketch_object_id"]
    )
    del sketch["placement"]
    try:
        resolve_loft_composite_guide(
            data,
            records,
            selected["selection_record_object_id"],
            feature["object_id"],
            altered,
        )
    except ValueError as error:
        report["negative_checks"].append(
            {"check": "Missing source placement", "passed": True, "reason": str(error)}
        )
    else:
        raise AssertionError("Missing source placement accepted")
    report["limitations"] = [
        "Observed source sequences are same-sketch tangent Line then Arc, or one open FittedSpline. Other sequences, cross-sketch, closed and BRep paths are rejected.",
        "Wrapper requires open solid NewBody with two Free profile sections and exactly one guide; spline rails, point ends and other operations remain unverified.",
        "Descriptor order is decoded. Path per-member opposed flags/traversal and connected-discovery options are not decoded from invariant secondary bytes.",
        "Natural source geometry and exact NURBS point/derivative evaluation are reported in parent component coordinates; no assembly/joint solving or Loft surface regeneration.",
        "Spline length is not derived from sparse samples; actual API length remains evidence only.",
    ]
    return report


if __name__ == "__main__":

    # explicit cli options prevent validation from relying on implicit runtime state
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate", action="store_true", required=True)
    parser.add_argument("--zstd-library", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("loft-composite-guide-decoding.json"),
    )

    # parsed arguments keep offline fixture inputs separate from live application control
    args = parser.parse_args()

    # saved fixture evidence records verified behavior without claiming procedural reconstruction
    report = validate_fixtures(Path(__file__).resolve().parent, args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "samples": len(report["samples"]),
                "negative_checks": len(report["negative_checks"]),
                "output": str(args.output),
            }
        )
    )
