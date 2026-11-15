import hashlib
import math
import struct


GENERATIONS = (18000, 19000)
PRINCIPAL_PLANES = (2, 3, 4)
IDENTITY_BASIS = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))


def support_candidates(data, start, end, stream):
    if not 0 <= start <= end <= len(data):
        raise ValueError("sketch support evidence span is outside its stream")
    candidates = []
    for offset in range(start, max(start, end - 18)):
        generation, plane, opaque_tag, null, axis, flag = struct.unpack_from("<IIIHIB", data, offset)
        if generation not in GENERATIONS or plane not in PRINCIPAL_PLANES:
            continue
        if null != 0 or axis != 5 - plane or flag not in (0, 1):
            continue
        length = 19 + 72 * flag
        if offset + length > end:
            continue
        basis = IDENTITY_BASIS
        if flag:
            rows = struct.unpack_from("<9d", data, offset + 19)
            basis = tuple(tuple(rows[column + row * 3] for row in range(3)) for column in range(3))
            if not orthonormal(basis):
                continue
        candidates.append({
            "status": "unqualified_layout_candidate",
            "record_class": "moCompRefPlane_c",
            "class_reference_resolution": "not_established",
            "generation_stamp": generation,
            "plane_object_id": plane,
            "opaque_reference_tag_u32": opaque_tag,
            "axis_code": axis,
            "basis_present": bool(flag),
            "basis_columns": basis,
            "source": {
                "stream": stream, "offset": offset, "length": length,
                "sha256": hashlib.sha256(data[offset:offset + length]).hexdigest(),
            },
        })
    return candidates


def orthonormal(basis):
    if not all(math.isfinite(value) for vector in basis for value in vector):
        return False
    for first in range(3):
        for second in range(3):
            product = sum(left * right for left, right in zip(basis[first], basis[second], strict=True))
            if not math.isclose(product, float(first == second), rel_tol=0, abs_tol=1e-9):
                return False
    cross = (
        basis[0][1] * basis[1][2] - basis[0][2] * basis[1][1],
        basis[0][2] * basis[1][0] - basis[0][0] * basis[1][2],
        basis[0][0] * basis[1][1] - basis[0][1] * basis[1][0],
    )
    return all(math.isclose(left, right, rel_tol=0, abs_tol=1e-9) for left, right in zip(cross, basis[2], strict=True))


def require_support_candidates(findings):
    planes = {"Front Plane": 2, "Top Plane": 3, "Right Plane": 4}
    seen = 0
    yz_seen = 0
    for capture in findings:
        for comparison in capture["comparisons"]:
            field = comparison["field"]
            if not field.startswith("neutral.sketch.") or not field.endswith(".support_name"):
                continue
            name = field[len("neutral.sketch."):-len(".support_name")]
            sketches = [sketch for sketch in capture["native"]["sketches"] if sketch["name"] == name]
            if len(sketches) != 1:
                raise ValueError(f"support evidence has no unique native sketch: {capture['asset']['path']}:{name}")
            candidates = sketches[0]["support_evidence"]
            if len(candidates) != 1 or candidates[0]["plane_object_id"] != planes.get(comparison["expected"]):
                raise ValueError(f"support candidate differs from the measured plane: {capture['asset']['path']}:{name}")
            if candidates[0]["status"] != "unqualified_layout_candidate" or candidates[0]["class_reference_resolution"] != "not_established":
                raise ValueError("support layout inventory cannot establish semantic qualification")
            seen += 1
            yz_seen += comparison["expected"] == "Right Plane"
    if seen != 25 or yz_seen != 3:
        raise ValueError(f"support inventory requires 25 principal-plane sketches including three YZ variants, found {seen}/{yz_seen}")
    print(f"Recorded {seen} unqualified support-layout candidates including {yz_seen} measured YZ variants; native class ownership remains unproved")
    require_cut_support(findings)


def require_cut_support(findings):
    required = {
        "native.sketch.CutSketch.support_kind",
        "neutral.sketch.CutSketch.face_selection_present",
        "neutral.sketch.CutSketch.face_producer",
    }
    seen = 0
    for capture in findings:
        if capture["recipe_id"] != "P04":
            continue
        seen += 1
        rows = [row for row in capture["comparisons"] if row["field"] in required]
        matched = {row["field"] for row in rows if row["status"] == "matched"}
        if len(rows) != len(required) or matched != required:
            raise ValueError(f"Cut face support differs from the measured fixture: {capture['asset']['path']}")
    if seen != 11:
        raise ValueError(f"support check requires 11 measured P04 cuts, found {seen}")
    print(f"Verified native face support and its neutral sketch producer in {seen} P04 captures")
