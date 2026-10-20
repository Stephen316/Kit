"""Observed sketch transforms and offset/angle construction plane geometry.

Matrices are row-major and act on column vectors, with translation in cm.
Direction is established by comparing sketchToModelSpace API coordinates;
assembly occurrence transforms are not decoded here.
"""

import math
import struct

from decode_parameters import read_string
from decode_sketch import attributes, numbers, reference, same


IDENTITY = [1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def rigid_matrix(values):
    if len(values) != 16 or not all(math.isfinite(v) for v in values):
        raise ValueError("Non-finite transform")
    if not same(values[12:], [0, 0, 0, 1]):
        raise ValueError("Not an observed affine transform")
    axes = [[values[row*4+column] for row in range(3)] for column in range(3)]
    if not same([sum(v*v for v in axis) for axis in axes], [1, 1, 1]):
        raise ValueError("Non-unit transform axes")
    if not same(cross(axes[0], axes[1]), axes[2]):
        raise ValueError("Not an observed rigid orientation")
    return values


def transform_point(matrix, point):
    return [sum(matrix[row*4+c] * point[c] for c in range(3)) + matrix[row*4+3]
            for row in range(3)]


def transform_vector(matrix, vector):
    return [sum(matrix[row*4+c] * vector[c] for c in range(3)) for row in range(3)]


def construction_planes(data, records, features):
    """Resolve the separate named plane object through reciprocal references."""
    planes = {f["object_id"]: f for f in features if f["kind"] == "ConstructionPlane"}
    decoded = set()
    for feature in planes.values():
        record = next(r for r in records if r.start == feature["record_offset"])
        body = data[record.body:record.end]
        try:
            # This reference was observed in both offset and angle plane features.
            plane_id = reference(body, 19)
        except (ValueError, struct.error):
            continue
        candidates = []
        for root in records:
            if root.object_id != plane_id:
                continue
            chunk = data[root.body:root.end]
            try:
                if chunk[:2] != b"\0\x01":
                    continue
                props, cursor = attributes(chunk, 2)
                if props != {"EntityGenesis": 0} or chunk[cursor+20] != 0:
                    continue
                mode = struct.unpack_from("<I", chunk, cursor)[0]
                if mode not in (1, 2):
                    continue
                coords = numbers(chunk, cursor+21, 9)
                origin, x_axis, y_axis = coords[:3], coords[3:6], coords[6:]
                normal = cross(x_axis, y_axis)
                matrix = [x_axis[0], y_axis[0], normal[0], origin[0],
                          x_axis[1], y_axis[1], normal[1], origin[1],
                          x_axis[2], y_axis[2], normal[2], origin[2], 0., 0., 0., 1.]
                rigid_matrix(matrix)
                _, end = read_string(chunk, cursor+109)
                reference(chunk, end)
                index = struct.unpack_from("<Q", chunk, end+11)[0]
                if reference(chunk, end+20) != feature["object_id"] or index != feature["stored_index"]:
                    continue
                if chunk[end+19] != 0 or chunk[end+31:end+33] != b"\0\x01":
                    continue
                name, _ = read_string(chunk, end+33)
                candidates.append({"name": name or None, "plane_object_id": plane_id,
                                   "plane_definition": "Offset" if mode == 1 else "Angle",
                                   "origin_cm": origin, "x_axis": x_axis, "y_axis": y_axis,
                                   "normal": normal, "plane_to_component_matrix": matrix,
                                   "coordinate_units": "cm",
                                   "decode_level": "Observed plane geometry, definition kind and parameters",
                                   "unresolved_inputs": ["Support plane/axis selection"],
                                   "selection_status": "Referenced support plane/axis not decoded"})
            except (ValueError, UnicodeError, struct.error, IndexError):
                continue
        if len(candidates) == 1:
            feature.update(candidates[0])
            decoded.add(feature["object_id"])
    return len(decoded)


def decode_placement(data, records, features):
    plane_count = construction_planes(data, records, features)
    resolved, unresolved = [], []
    for feature in features:
        if feature["kind"] != "Sketch":
            continue
        candidates = []
        for root in records:
            if root.object_id != feature["sketch_object_id"]:
                continue
            body = data[root.body:root.end]
            try:
                name, _ = read_string(body, 28)
                if name != (feature["name"] or ""):
                    continue
                transform_id = reference(body, 0)
                for record in records:
                    if record.object_id != transform_id:
                        continue
                    chunk = data[record.body:record.end]
                    if chunk[:2] != b"\0\0" or len(chunk) not in (15, 143):
                        continue
                    reference(chunk, len(chunk)-11)
                    if chunk[-12] != 0:
                        continue
                    if len(chunk) == 15 and chunk[2] == 1:
                        matrix = list(IDENTITY)
                        encoding = "ImplicitIdentity"
                    elif len(chunk) == 143 and chunk[2] == 0:
                        matrix = rigid_matrix(numbers(chunk, 3, 16))
                        encoding = "ExplicitFloat64Matrix"
                    else:
                        continue
                    candidates.append({"sketch_to_component_matrix": matrix,
                                       "matrix_order": "row-major; column-vector multiplication",
                                       "translation_units": "cm", "encoding": encoding,
                                       "transform_object_id": transform_id,
                                       "record_offset": record.start,
                                       "scope": "Parent component; assembly occurrences unresolved"})
            except (ValueError, UnicodeError, struct.error):
                continue
        if len(candidates) != 1:
            unresolved.append(feature["object_id"])
            feature["placement_status"] = "Undecoded or ambiguous transform"
            continue
        placement = candidates[0]
        feature["placement"] = placement
        feature["placement_status"] = "Observed rigid transform decoded"
        matrix = placement["sketch_to_component_matrix"]
        for geometry in feature.get("geometry", []):
            for key in ("position_cm", "start_cm", "end_cm", "center_cm"):
                if key in geometry:
                    geometry["component_"+key] = transform_point(matrix, geometry[key])
            for key in ("normal", "reference_axis", "major_axis", "minor_axis"):
                if key in geometry:
                    geometry["component_"+key] = transform_vector(matrix, geometry[key])
        resolved.append(feature["object_id"])
    return {"decoded_sketch_placements": len(resolved), "unresolved_sketches": unresolved,
            "decoded_construction_planes": plane_count,
            "scope": "Observed rigid sketch transforms and offset/angle plane geometry"}
