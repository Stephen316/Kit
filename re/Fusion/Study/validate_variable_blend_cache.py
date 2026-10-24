"""Focused saved variable-blend cache, endpoint and boundedness evidence."""

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from asm_records import inspect_asm
from decode_brep import decode_topology
from decode_bspline import decode_bspline, evaluate_curve, evaluate_surface
from decode_pcurve import evaluate_pcurve
from decode_variable_blend_cache import decode_variable_blend_cache
from fusion_archive import read_members
from validate_fillet_spline_caches import OLD_CACHE_HASHES

# saved fixture paths remain relative to the checked validator source
ROOT = Path(__file__).resolve().parent

# fixed captures prevent validation coverage from drifting with corpus growth
FILES = [
    "edgemodes-87edbf67527b/fillet_chord.f3d",
    "edgemodes-87edbf67527b/fillet_asymmetric.f3d",
]


# stored blend approximations need bounded evaluation without inventing parameter correspondence
def validate(zstd_library):
    truth = json.loads((ROOT / "edgemodes-87edbf67527b/ground_truth.json").read_text())
    api = {s["file"]: s for s in truth["samples"]}
    report = {
        "scope": "Two observed planar-support srf_srf_v_bl_spl_sur rational bicubic approximation caches",
        "integration": {
            "helper": "decode_variable_blend_cache.decode_variable_blend_cache(record)",
            "dispatch": "In decode_bspline, before unsupported procedural rejection: spline-surface with subtype srf_srf_v_bl_spl_sur -> this helper. Preserve all existing defaults/other branches.",
            "output": "Same rational tensor-cache schema used by evaluate_surface, plus literal procedural prefix, spine cache when present, native mode/flags and separate cache-domain/trim bounds.",
            "shared_files_changed_by_this_task": False,
            "validation_command": "/usr/bin/python3 validate_variable_blend_cache.py",
        },
        "native_framing": {
            "supports": "Two consecutive typed blend_support_surface/plane descriptions, bounded fixed-width fields and absent optional curves, preserved without reconstructing the exact blend.",
            "chord_spine": "Bounded embedded degree-five exact_int_cur NUBS subtype; complete cache is parsed by the existing exact-curve reader, then one fixed_width description.",
            "asymmetric_spine": "Explicit straight description with finite bounds, then two edge_offset descriptions.",
            "grid": "Explicit nurbs/degree3/degree3/both marker and four enum0 flags; counted U/V compact knots; four doubles per rational control; U-fast to V-fast normalization.",
            "trailer": "Scalar, six counted scalar lists, literal boolean/integer fields, null_curve, literal flags, nullbs/nullbs, exact subtype end, four finite bounds, exact record exhaustion.",
        },
        "samples": [],
        "compatibility": [],
        "guards": [],
        "strict_domain_guards": [],
        "limitations": [
            "API truth captured Fillet settings, not surface-cache or evaluator getters. No exact procedural surface or approximation-error bound is claimed.",
            "The two observed support/spine/mode combinations are bounded independently. Other support types, rational weights layouts, wrapper variants and procedural blend types remain unsupported.",
            "Surface and XYZ/UV caches can disagree at interior samples. Values are reported as corroboration of stored approximations, not exact curve/surface equality.",
            "Edge32 has negative XYZ parameter bounds but positive UV-cache bounds with opposite endpoint order. Parameter correspondence and flag semantics remain unresolved; no automatic remapping is applied.",
            "Endpoint set agreement is checked only after explicit coedge/loop/face and edge/vertex/point identity links. Geometry is never used to choose persistent identities or owners.",
            "Raw ASM coordinates are retained; current visibility, lifecycle, assembly solving, placement and regeneration are unresolved.",
        ],
    }
    sources = {}
    for relative in FILES:
        members = read_members(ROOT / relative, zstd_library)
        member, raw = next(
            (m, raw) for m, raw in members.items() if m.endswith(".smbh")
        )
        parsed = inspect_asm(raw)
        assert parsed["complete_token_stream"]
        source = parsed["records"][10]
        cache = decode_variable_blend_cache(source)
        sources[relative] = source
        assert (cache["degree_u"], cache["degree_v"], cache["control_count_u"]) == (
            3,
            3,
            4,
        )
        expected_v = 21 if relative.endswith("fillet_chord.f3d") else 31
        assert cache["control_count_v"] == expected_v
        assert (
            len(cache["weights"]) == len(cache["raw_control_points"]) == 4 * expected_v
        )
        assert min(cache["weights"]) > 0 and min(cache["weights"]) < 1
        topology = decode_topology(parsed)
        nodes = {n["index"]: n for n in topology["nodes"]}
        sample = {
            "file": relative,
            "member": member,
            "record_index": 10,
            "record_offset": source["offset"],
            "actual_api_settings": api[Path(relative).name]["settings"],
            "cache": cache,
            "parent_linked_boundary_checks": [],
            "independent_api_surface_evaluator_captured": False,
        }
        ua, ub = cache["stored_parameter_interval_u"]
        va, vb = cache["stored_parameter_interval_v"]
        samples = [
            evaluate_surface(cache, ua + (ub - ua) * i / 4, va + (vb - va) * j / 4)
            for i in range(5)
            for j in range(5)
        ]
        assert all(math.isfinite(c) for point in samples for c in point)
        sample["finite_surface_grid"] = {"evaluations": 25, "raw_points": samples}
        for coedge in nodes.values():
            if coedge["kind"] != "coedge":
                continue
            loop = nodes[coedge["loop_index"]]
            face = nodes[loop["face_index"]]
            if face["surface_index"] != 10:
                continue
            assert loop["kind"] == "loop" and face["kind"] == "face"
            edge = nodes[coedge["edge_index"]]
            assert edge["kind"] == "edge"
            uv = nodes[coedge["pcurve_index"]]["uv_curve"]
            endpoints = []
            for which in ("start", "end"):
                vertex = nodes[edge[which + "_vertex_index"]]
                point = nodes[vertex["point_index"]]
                assert vertex["kind"] == "vertex" and point["kind"] == "point"
                endpoints.append(
                    {
                        "vertex_index": vertex["index"],
                        "point_index": point["index"],
                        "raw_position": point["raw_origin"],
                    }
                )
            uv_surface = [
                evaluate_surface(cache, *evaluate_pcurve(uv, p))
                for p in uv["parameter_domain"]
            ]
            stored = [p["raw_position"] for p in endpoints]

            set_error = max(
                max(min(math.dist(a, b) for b in stored) for a in uv_surface),
                max(min(math.dist(a, b) for b in uv_surface) for a in stored),
            )
            assert set_error < 1e-9
            edge_params = [edge["start_parameter"], edge["end_parameter"]]
            same_params = all(
                math.isclose(a, b, abs_tol=1e-12)
                for a, b in zip(edge_params, uv["parameter_domain"])
            )
            check = {
                "coedge_index": coedge["index"],
                "loop_index": loop["index"],
                "face_index": face["index"],
                "surface_index": 10,
                "edge_index": edge["index"],
                "pcurve_index": coedge["pcurve_index"],
                "curve_index": edge["curve_index"],
                "explicit_edge_endpoints": endpoints,
                "uv_domain_surface_endpoints": uv_surface,
                "unordered_endpoint_set_error_raw": set_error,
                "edge_parameter_interval": edge_params,
                "uv_cache_parameter_domain": uv["parameter_domain"],
                "stored_parameter_intervals_numerically_agree": same_params,
                "parameter_correspondence": "No inferred remapping; intervals retained literally",
            }
            if same_params and "bspline_curve" in nodes.get(edge["curve_index"], {}):
                xyz = nodes[edge["curve_index"]]["bspline_curve"]
                common_start = max(
                    min(edge_params),
                    uv["parameter_domain"][0],
                    xyz["parameter_domain"][0],
                )
                common_end = min(
                    max(edge_params),
                    uv["parameter_domain"][1],
                    xyz["parameter_domain"][1],
                )
                assert common_start < common_end
                parameters = (
                    [common_start]
                    + [
                        common_start + (common_end - common_start) * fraction
                        for fraction in (0.25, 0.5, 0.75)
                    ]
                    + [common_end]
                )
                assert all(
                    uv["parameter_domain"][0] <= p <= uv["parameter_domain"][1]
                    and xyz["parameter_domain"][0] <= p <= xyz["parameter_domain"][1]
                    for p in parameters
                )
                deviations = []
                for parameter in parameters:
                    surface_point = evaluate_surface(
                        cache, *evaluate_pcurve(uv, parameter)
                    )
                    deviations.append(
                        math.dist(surface_point, evaluate_curve(xyz, parameter))
                    )
                assert max(deviations[0], deviations[-1]) < 1e-9
                check["five_sample_xyz_surface_cache_deviations_raw"] = deviations
                check["sampled_common_cache_parameter_domain"] = [
                    common_start,
                    common_end,
                ]
                check["sample_parameters"] = parameters
                check["comparison_scope"] = (
                    "Samples are generated inside the literal intersection of both cache domains and the EDGE interval; native endpoints are unchanged and no clamping or parameter remapping is applied"
                )
                if min(edge_params) < uv["parameter_domain"][0]:
                    assert math.isclose(
                        min(edge_params), uv["parameter_domain"][0], abs_tol=1e-12
                    )
                    try:
                        evaluate_pcurve(uv, min(edge_params))
                    except ValueError as error:
                        assert str(error) == "Parameter outside the stored NURBS domain"
                        report["strict_domain_guards"].append(
                            {
                                "file": relative,
                                "coedge_index": coedge["index"],
                                "edge_index": edge["index"],
                                "literal_edge_parameter": min(edge_params),
                                "literal_uv_domain_start": uv["parameter_domain"][0],
                                "strict_outside_domain_rejected": True,
                                "reason": str(error),
                            }
                        )
                    else:
                        raise AssertionError(
                            "Out-of-domain EDGE parameter was silently accepted by the UV evaluator"
                        )
            sample["parent_linked_boundary_checks"].append(check)
        assert len(sample["parent_linked_boundary_checks"]) == 4
        assert any(
            c["edge_index"] == 32
            and not c["stored_parameter_intervals_numerically_agree"]
            for c in sample["parent_linked_boundary_checks"]
        )
        report["samples"].append(sample)

    controls = [
        next(
            c
            for c in OLD_CACHE_HASHES
            if c["file"].startswith("moretools") and c["index"] == 18
        ),
        next(
            c
            for c in OLD_CACHE_HASHES
            if c["file"].startswith("splinepatches") and c["index"] == 11
        ),
        next(
            c
            for c in OLD_CACHE_HASHES
            if c["file"].startswith("splines") and c["index"] == 18
        ),
    ]
    for control in controls:
        members = read_members(ROOT / control["file"], zstd_library)
        record = inspect_asm(members[control["member"]])["records"][control["index"]]
        digest = hashlib.sha256(
            json.dumps(decode_bspline(record), sort_keys=True).encode()
        ).hexdigest()
        assert digest == control["sha256"]
        try:
            decode_variable_blend_cache(record)
        except (ValueError, IndexError):
            pass
        else:
            raise AssertionError("Distinct procedural control accepted")
        report["compatibility"].append(
            dict(
                control, exact_old_output=True, new_helper_rejects_distinct_subtype=True
            )
        )

    # invalid native inputs must stay rejected despite expanded decoder coverage
    def reject(label, file_index, mutate):
        record = copy.deepcopy(sources[FILES[file_index]])
        mutate(record["tokens"])
        try:
            decode_variable_blend_cache(record)
        except (ValueError, IndexError) as error:
            report["guards"].append(
                {"case": label, "rejected": True, "reason": str(error)}
            )
        else:
            raise AssertionError("Malformed variable blend accepted: " + label)

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject(
        "Support plane entity type changed",
        1,
        lambda t: t[8].update(value="unknown_surface"),
    )

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject("Embedded spine subtype terminator missing", 0, lambda t: t.__delitem__(179))

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject("Spine and width mode disagree", 1, lambda t: t[48].update(value=0))

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject("Rational weight nonpositive", 1, lambda t: t[116].update(value=0.0))

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject(
        "Compact knot multiplicity exceeds degree", 1, lambda t: t[84].update(value=4)
    )

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject("Nonfinite grid coordinate", 1, lambda t: t[113].update(value=float("nan")))

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject(
        "Wrong trailer subtype terminator",
        1,
        lambda t: t[627].update(kind="subtype_start"),
    )

    # malformed native inputs must remain explicit failures rather than usable evidence
    reject("Trim bound outside cache domain", 1, lambda t: t[635].update(value=10.0))
    checks = [
        c
        for sample in report["samples"]
        for c in sample["parent_linked_boundary_checks"]
    ]
    interior_errors = [
        v
        for c in checks
        for v in c.get("five_sample_xyz_surface_cache_deviations_raw", [])[1:-1]
    ]
    report["summary"] = {
        "saved_files": 2,
        "new_surface_caches": 2,
        "rational_controls_decoded": 84 + 124,
        "finite_surface_grid_evaluations": 50,
        "explicit_parent_boundary_chains": len(checks),
        "endpoint_set_checks": len(checks),
        "endpoint_points_corroborated": len(checks) * 2,
        "parameter_interval_counterexamples_retained": sum(
            not c["stored_parameter_intervals_numerically_agree"] for c in checks
        ),
        "maximum_endpoint_set_error_raw": max(
            c["unordered_endpoint_set_error_raw"] for c in checks
        ),
        "maximum_sampled_interior_xyz_surface_cache_deviation_raw": max(
            interior_errors
        ),
        "old_cache_controls_unchanged": len(controls),
        "malformed_guards": len(report["guards"]),
        "strict_evaluator_domain_guards": len(report["strict_domain_guards"]),
    }
    assert report["summary"]["strict_evaluator_domain_guards"] == 1
    return report


if __name__ == "__main__":

    # explicit command line arguments keep reference inputs and report destinations configurable
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="variable-blend-cache-decoding.json")

    # parsed options preserve caller control over validation inputs and outputs
    args = parser.parse_args()

    # explicit compression discovery permits saved archive checks without launching fusion
    zstd = next(
        Path(
            "/Users/stephenh/Library/Application Support/Autodesk/webdeploy/production"
        ).glob(
            "*/Autodesk Fusion.app/Contents/Frameworks/Python.framework/Versions/3.14/lib/libzstd.1.5.7.dylib"
        )
    )

    # one report retains validation evidence for independent audit review
    report = validate(str(zstd))
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))
