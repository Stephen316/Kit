"""Offline rational curve, derivative and tensor arithmetic regression checks."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

from decode_bspline import evaluate_surface
from decode_loft_composite_guides import _nurbs_derivative
from decode_nurbs import evaluate_nurbs, numeric_array

# locate saved fixtures without depending on the caller s current directory
ROOT = Path(__file__).resolve().parent


# compare independent finite references without accepting matching infinities or nan values
def _near(actual, expected):
    if isinstance(expected, (list, tuple)):
        return len(actual) == len(expected) and all(
            _near(a, b) for a, b in zip(actual, expected)
        )
    return math.isfinite(actual) and math.isclose(
        actual,
        expected,
        rel_tol=2e-12,
        abs_tol=0.0 if 0 < abs(expected) < 1e-200 else 2e-12,
    )


# build a bilinear tensor whose independently known value is an affine coordinate pair
def _surface(weights):
    return dict(
        degree_u=1,
        degree_v=1,
        control_count_u=2,
        control_count_v=2,
        raw_control_points=[
            [2.0, 0.0, 0.0],
            [2.0, 1.0, 0.0],
            [3.0, 0.0, 0.0],
            [3.0, 1.0, 0.0],
        ],
        knots_u=[0.0, 0.0, 1.0, 1.0],
        knots_v=[0.0, 0.0, 1.0, 1.0],
        parameter_domain_u=[0.0, 1.0],
        parameter_domain_v=[0.0, 1.0],
        weights=weights,
    )


# exercise rational scale invariance before testing the same change in native source bytes
def validate(zstd=None):
    checks, guards, native = [], [], []

    # retain each analytic comparison as an independently named regression check
    def check(label, actual, expected):
        if not _near(actual, expected):
            raise AssertionError((label, actual, expected))
        checks.append(dict(name=label, actual=actual, expected=expected))

    # require malformed operands or unrepresentable derivatives to become explicit errors
    def reject(label, operation):
        try:
            operation()
        except ValueError as error:
            guards.append(dict(name=label, reason=str(error)))
        else:
            raise AssertionError(label + " accepted")

    linear = dict(
        degree=1,
        knots=[0.0, 0.0, 1.0, 1.0],
        control_points_cm=[[2.0, 0.0, 0.0], [3.0, 1.0, 0.0]],
        parameter_domain=[0.0, 1.0],
    )
    cubic = dict(
        degree=3,
        knots=[0.0] * 4 + [1.0] * 4,
        control_points_cm=[
            [0.0, 0.0, 0.0],
            [1.0, 2.0, 0.0],
            [2.0, 2.0, 0.0],
            [3.0, 0.0, 0.0],
        ],
        parameter_domain=[0.0, 1.0],
    )
    middle_weight = math.sqrt(0.5)
    quarter_circle = dict(
        degree=2,
        knots=[0.0] * 3 + [1.0] * 3,
        control_points_cm=[[1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]],
        parameter_domain=[0.0, 1.0],
    )
    for scale in (1.0, 5e-324, 1e-170, 1e170, 1e308):
        line = dict(linear, weights=[scale] * 2)
        curve = dict(cubic, weights=[scale] * 4)
        check(
            str(scale) + " linear position", evaluate_nurbs(line, 0.5), [2.5, 0.5, 0.0]
        )
        check(
            str(scale) + " linear derivative",
            _nurbs_derivative(line, 0.5),
            [1.0, 1.0, 0.0],
        )
        check(
            str(scale) + " cubic position", evaluate_nurbs(curve, 0.5), [1.5, 1.5, 0.0]
        )
        check(
            str(scale) + " cubic derivative",
            _nurbs_derivative(curve, 0.5),
            [3.0, 0.0, 0.0],
        )
        check(
            str(scale) + " cubic start derivative",
            _nurbs_derivative(curve, 0.0),
            [3.0, 6.0, 0.0],
        )
        check(
            str(scale) + " cubic end derivative",
            _nurbs_derivative(curve, 1.0),
            [3.0, -6.0, 0.0],
        )
        check(
            str(scale) + " bilinear surface",
            evaluate_surface(_surface([scale] * 4), 0.5, 0.5),
            [2.5, 0.5, 0.0],
        )
        if scale != 5e-324:
            arc = dict(quarter_circle, weights=[scale, middle_weight * scale, scale])
            check(
                str(scale) + " rational quarter-circle position",
                evaluate_nurbs(arc, 0.5),
                [middle_weight, middle_weight, 0.0],
            )
            derivative = 2.0 / (1.0 + middle_weight)
            check(
                str(scale) + " rational quarter-circle derivative",
                _nurbs_derivative(arc, 0.5),
                [-derivative, derivative, 0.0],
            )

    for degree in (10, 23):
        for scale in (1.0, 1e308):
            high_degree = dict(
                degree=degree,
                knots=[0.0] * (degree + 1) + [1.0] * (degree + 1),
                control_points_cm=[
                    [float(i), float(i * i), 0.0] for i in range(degree + 1)
                ],
                parameter_domain=[0.0, 1.0],
                weights=[scale] * (degree + 1),
            )
            check(
                str(degree) + " degree position " + str(scale),
                evaluate_nurbs(high_degree, 0.5),
                [degree / 2.0, degree * (degree + 1) / 4.0, 0.0],
            )
            check(
                str(degree) + " degree derivative " + str(scale),
                _nurbs_derivative(high_degree, 0.5),
                [float(degree), float(degree * degree), 0.0],
            )

    for scale in (1.0, 1e308):
        high_surface = _surface([scale] * 22)
        high_surface.update(
            degree_u=10,
            control_count_u=11,
            knots_u=[0.0] * 11 + [1.0] * 11,
            raw_control_points=[
                [float(i), float(j), 0.0] for i in range(11) for j in (0, 1)
            ],
        )
        check(
            "High degree tensor position " + str(scale),
            evaluate_surface(high_surface, 0.5, 0.5),
            [5.0, 0.5, 0.0],
        )
    intermediate = _surface([1e-200] * 4)
    intermediate["raw_control_points"] = [
        [0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 1.0, 0.0],
    ]
    check(
        "Tensor homogeneous underflow waits for final projective division",
        evaluate_surface(intermediate, 1e-210, 0.5),
        [1e-210, 0.5, 0.0],
    )
    from decimal import Inexact, localcontext

    with localcontext() as context:
        context.prec = 7
        context.Emax = 17
        context.Emin = -17
        context.traps[Inexact] = True
        check(
            "Caller decimal context cannot alter curve recovery",
            evaluate_nurbs(dict(linear, weights=[1e308] * 2), 0.5),
            [2.5, 0.5, 0.0],
        )
        check(
            "Caller decimal context cannot alter tensor recovery",
            evaluate_surface(_surface([1e308] * 4), 0.5, 0.5),
            [2.5, 0.5, 0.0],
        )

    mixed = dict(
        linear,
        control_points_cm=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        weights=[1e-308, 1e308],
    )
    check(
        "Mixed-scale curve retains tiny-weight start",
        evaluate_nurbs(mixed, 0.0),
        [1.0, 0.0, 0.0],
    )
    check(
        "Mixed-scale curve retains dominant interior",
        evaluate_nurbs(mixed, 0.5),
        [0.0, 1.0, 0.0],
    )
    check("Mixed-scale curve retains end", evaluate_nurbs(mixed, 1.0), [0.0, 1.0, 0.0])
    mixed_surface = _surface([1e-308, 1e308, 1e308, 1e308])
    mixed_surface["raw_control_points"] = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]
    check(
        "Mixed-scale surface retains tiny-weight corner",
        evaluate_surface(mixed_surface, 0.0, 0.0),
        [1.0, 0.0, 0.0],
    )
    check(
        "Mixed-scale surface interior",
        evaluate_surface(mixed_surface, 0.5, 0.5),
        [1.0 / 3.0, 2.0 / 3.0, 0.0],
    )
    check(
        "Mixed-scale surface final corner",
        evaluate_surface(mixed_surface, 1.0, 1.0),
        [0.0, 1.0, 0.0],
    )
    wide = dict(
        linear,
        knots=[-1e308, -1e308, 1e308, 1e308],
        parameter_domain=[-1e308, 1e308],
        control_points_cm=[[0.0, 0.0, 0.0], [2.0, 4.0, 0.0]],
        weights=[],
    )
    check(
        "Finite knot subtraction wider than binary64",
        evaluate_nurbs(wide, 0.0),
        [1.0, 2.0, 0.0],
    )
    check(
        "Wide-knot exact derivative",
        _nurbs_derivative(wide, 0.0),
        [1e-308, 2e-308, 0.0],
    )
    constant = dict(
        degree=0,
        knots=[0.0, 1.0],
        parameter_domain=[0.0, 1.0],
        control_points_cm=[[2.0, 3.0, 4.0, 5.0]],
        weights=[],
    )
    check(
        "Degree-zero four-dimensional intermediate",
        evaluate_nurbs(constant, 0.5),
        [2.0, 3.0, 4.0, 5.0],
    )
    one_axis = _surface([1e308, 1e308])
    one_axis.update(
        degree_u=0,
        control_count_u=1,
        knots_u=[0.0, 1.0],
        raw_control_points=[[2.0, 0.0, 0.0], [2.0, 1.0, 0.0]],
    )
    check(
        "Degree-zero tensor axis", evaluate_surface(one_axis, 0.5, 0.5), [2.0, 0.5, 0.0]
    )

    huge = dict(
        linear, control_points_cm=[[-1e308, 0.0, 0.0], [1e308, 0.0, 0.0]], weights=[]
    )
    check(
        "Large opposite coordinates cancel finitely",
        evaluate_nurbs(huge, 0.5),
        [0.0, 0.0, 0.0],
    )

    # derived overflow must remain explicit rather than returning infinite geometry
    reject("Unrepresentable derived derivative", lambda: _nurbs_derivative(huge, 0.5))

    # endpoint derivatives must report physical overflow without discarding tiny source weights
    reject(
        "Unrepresentable mixed-weight endpoint derivative",
        lambda: _nurbs_derivative(mixed, 0.0),
    )
    bad = dict(linear, weights=[0.0, 1.0])

    # invalid rational weights must fail before homogeneous evaluation can divide by zero
    reject("Nonpositive rational weight", lambda: evaluate_nurbs(bad, 0.5))
    bad_point = dict(
        linear, weights=[], control_points_cm=[[math.nan, 0.0, 0.0], [1.0, 0.0, 0.0]]
    )

    # nonfinite source coordinates must never become published geometric results
    reject("Nonfinite source point", lambda: evaluate_nurbs(bad_point, 0.5))

    # stored knot bounds must prevent unsupported surface extrapolation
    reject("Out-of-domain parameter", lambda: evaluate_surface(_surface([]), -0.1, 0.5))

    if zstd is not None:
        native = _native_weight_controls(zstd, check)
    source_files = (
        "decode_nurbs.py",
        "decode_bspline.py",
        "decode_loft_composite_guides.py",
        "validate_rational_numerics.py",
    )
    return dict(
        scope="Offline rational scale, tensor and derivative arithmetic; saved native source mutations use no main reader or live Fusion",
        checks=checks,
        guards=guards,
        native_weight_controls=native,
        summary=dict(
            checks=len(checks),
            guards=len(guards),
            native_weight_scale_controls=len(native),
            live_calls=0,
            main_reader_calls=0,
        ),
        source_sha256={
            name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in source_files
        },
    )


# mutate actual native weights while rebuilding canonical sources from the changed bytes
def _native_weight_controls(zstd, check):
    from decode_basics import attach_parameters, named_features
    from decode_parameters import decode_stream
    from decode_placement import decode_placement
    from decode_sketch import decode_sketches
    from decode_sweep_fixed_spline_paths import decode_sweep_fixed_spline_paths
    from validate_sweep_fixed_spline_sources import load_sources

    archive = "sweepnurbspaths-7ded30a4b9ae/rational_cubic.f3d"
    data, records, features, member, members = load_sources(ROOT, archive, zstd)
    original = decode_sweep_fixed_spline_paths(data, records, features)
    (row,) = original["decoded"]
    source = row["settings"]["path"]["native_source_evidence"]
    geometry = next(
        record
        for record in records
        if record.start == source["native_geometry_continuation_record_offset"]
    )
    payload = data[geometry.body : geometry.end]
    _, weights_cursor = numeric_array(payload, 75)
    weights, _ = numeric_array(payload, weights_cursor)
    observations = []
    for scale in (1e-170, 1e170, 1e308):
        changed = bytearray(data)
        scaled = [weight * scale for weight in weights]
        for index, weight in enumerate(scaled):
            struct.pack_into(
                "<d", changed, geometry.body + weights_cursor + 12 + 8 * index, weight
            )
        changed = bytes(changed)
        private = named_features(changed, records)
        parameters, _ = decode_stream(changed, records)
        attach_parameters(changed, records, private, parameters)
        decode_sketches(changed, records, private)
        decode_placement(changed, records, private)
        actual = decode_sweep_fixed_spline_paths(changed, records, private)
        if actual["unresolved"] or len(actual["decoded"]) != 1:
            raise AssertionError((scale, actual["unresolved"]))
        fresh = actual["decoded"][0]["settings"]["path"]["native_source_evidence"]
        check(
            str(scale) + " native source weight bytes retained",
            fresh["source_nurbs"]["weights"] == scaled,
            True,
        )
        for ordinal, (before, after) in enumerate(
            zip(source["natural_derived_samples"], fresh["natural_derived_samples"])
        ):
            check(
                str(scale) + " native point " + str(ordinal),
                after["point_sketch_local_cm"],
                before["point_sketch_local_cm"],
            )
            check(
                str(scale) + " native derivative " + str(ordinal),
                after["natural_parameter_derivative_sketch_local"],
                before["natural_parameter_derivative_sketch_local"],
            )
        observations.append(
            dict(
                archive=archive,
                geometry_record_offset=geometry.start,
                factor=scale,
                native_weights=scaled,
                source_selection_preserved=fresh["selection"] == source["selection"],
                derived_samples=5,
                mutation_scope="Native geometry bytes changed in memory; archive and saved API truth remain untouched",
            )
        )
    return observations


# write verification evidence to an explicit output without replacing captured stage reports
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zstd-library")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = validate(args.zstd_library)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
