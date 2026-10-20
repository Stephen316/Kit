"""Observed sketch entity layouts; sketch-local coordinates use centimetres.

These bounded fragment readers do not infer constraints from geometry or solve
them. Only explicitly stored, recognized constraint records are reported.
"""

import math
import struct


def ascii_string(data, position):
    length = struct.unpack_from("<I", data, position)[0]
    end = position + 4 + length
    if length > 256 or end > len(data):
        raise ValueError("Invalid attribute string")
    text = data[position + 4:end].decode("ascii")
    if not text.isprintable():
        raise ValueError("Invalid attribute text")
    return text, end


def attributes(data, position):
    count = struct.unpack_from("<I", data, position)[0]
    if count > 32:
        raise ValueError("Too many attributes")
    position += 4
    result = {}
    for _ in range(count):
        key, position = ascii_string(data, position)
        kind, position = ascii_string(data, position)
        if kind != "IntrinsicMetaTypeuint64" or key in result:
            raise ValueError("Unsupported attribute layout")
        result[key] = struct.unpack_from("<Q", data, position)[0]
        position += 8
    return result, position


def reference(data, position):
    if position < 0 or position + 11 > len(data):
        raise ValueError("Truncated reference")
    if data[position] != 1 or data[position + 9:position + 11] != b"\0\0":
        raise ValueError("Unsupported reference encoding")
    return struct.unpack_from("<Q", data, position + 1)[0]


def numbers(data, position, count):
    values = list(struct.unpack_from("<" + "d" * count, data, position))
    if not all(math.isfinite(v) for v in values):
        raise ValueError("Non-finite geometry")
    return values


def same(a, b):
    return len(a) == len(b) and all(math.isclose(x, y, abs_tol=1e-9, rel_tol=1e-9)
                                   for x, y in zip(a, b))


def constraint_prefix(body):
    if len(body) < 6 or body[0] != 1:
        raise ValueError("Not an observed constraint prefix")
    count = struct.unpack_from("<I", body, 1)[0]
    if not 1 <= count <= 16:
        raise ValueError("Unsupported constraint argument count")
    # Initial argument slots include four extra, currently uninterpreted bytes.
    inputs = [reference(body, 5 + index * 15) for index in range(count)]
    position = 5 + count * 15
    if position >= len(body) or body[position] != 1:
        raise ValueError("Missing constraint attributes")
    props, position = attributes(body, position + 1)
    return inputs, props, position


def decode_sketches(data, records, features):
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    for sketch in sketches.values():
        sketch.update({"coordinate_system": "sketch-local", "coordinate_units": "cm",
                       "geometry": [], "constraints": [], "dimensions": []})
    entities, curves, skipped = {}, [], []
    for record in records:
        body = data[record.body:record.end]
        if not body.startswith(b"\0\x01"):
            continue
        try:
            props, cursor = attributes(body, 2)
            if props.get("EntityGenesis") != 2:
                continue
            owner = reference(body, len(body) - 11)
            if owner not in sketches:
                continue
            item = {"object_id": record.object_id, "sketch_object_id": owner,
                    "record_offset": record.start}
            if "pt_tag" in props and len(body) - cursor == 99:
                item.update({"kind": "Point", "entity_tag": props["pt_tag"],
                             "position_cm": numbers(body, cursor + 19, 3)})
                entities[record.object_id] = item
            elif "crv_primary_id" in props:
                curves.append((record, body, props, cursor, item))
        except (ValueError, UnicodeError, struct.error):
            continue
    for record, body, props, cursor, item in curves:
        try:
            values = numbers(body, cursor, 12)
            origin = values[:3]
            first = reference(body, cursor + 96)
            if props.get("crv_secondary_id") != 0:
                raise ValueError("Secondary curve representation is unsupported")
            if len(body) - cursor == 171:
                start_id = reference(body, cursor + 107)
                start, end = entities[start_id], entities[first]
                if start["sketch_object_id"] != item["sketch_object_id"] or end["sketch_object_id"] != item["sketch_object_id"]:
                    raise ValueError("Cross-sketch endpoints")
                if not same(start["position_cm"], origin) or not same(
                    [x + y for x, y in zip(origin, values[3:6])], end["position_cm"]
                ):
                    raise ValueError("Line representation does not match endpoint references")
                item.update({"kind": "Line", "start_point_id": start_id, "end_point_id": first,
                             "start_cm": start["position_cm"], "end_cm": end["position_cm"]})
            elif len(body) - cursor == 162:
                center = entities[first]
                normal, axis = values[3:6], values[6:9]
                if center["sketch_object_id"] != item["sketch_object_id"] or not same(center["position_cm"], origin):
                    raise ValueError("Circle center reference does not match")
                if (values[9] <= 0 or not same(values[10:], [0, 2 * math.pi])
                        or not same([sum(x*x for x in normal), sum(x*x for x in axis),
                                     sum(x*y for x, y in zip(normal, axis))], [1, 1, 0])):
                    raise ValueError("Only the observed full-circle layout is supported")
                item.update({"kind": "Circle", "center_point_id": first, "center_cm": origin,
                             "radius_cm": values[9], "radius_mm": values[9] * 10,
                             "normal": normal, "reference_axis": axis})
            else:
                raise ValueError("Unrecognized curve record size")
            item["entity_tag"] = props["crv_primary_id"]
            entities[record.object_id] = item
        except (ValueError, KeyError, struct.error) as error:
            skipped.append({"object_id": record.object_id, "reason": str(error)})
    for entity in entities.values():
        sketches[entity["sketch_object_id"]]["geometry"].append(entity)
    unknown_constraints = []
    dimensions = []
    for record in records:
        body = data[record.body:record.end]
        try:
            inputs, props, cursor = constraint_prefix(body)
            if props.get("EntityGenesis") == 0:
                dimensions.append((record, body, inputs))
                continue
            if props.get("EntityGenesis") != 2:
                continue
            owner = reference(body, cursor)
            if owner not in sketches:
                continue
            cursor += 11
            code = struct.unpack_from("<Q", body, cursor)[0]
            count = struct.unpack_from("<I", body, cursor + 8)[0]
            if count != len(inputs):
                raise ValueError("Constraint argument copies differ")
            copied = [reference(body, cursor + 12 + 11*i) for i in range(count)]
            if copied != inputs or any(i not in entities or entities[i]["sketch_object_id"] != owner for i in inputs):
                raise ValueError("Constraint entity references do not resolve")
            kind = {64: "Horizontal", 128: "Vertical", 1: "Coincident"}.get(code)
            kinds = [entities[i]["kind"] for i in inputs]
            if ((kind in ("Horizontal", "Vertical") and kinds != ["Line"])
                    or (kind == "Coincident" and kinds != ["Point", "Point"]) or kind is None):
                unknown_constraints.append({"object_id": record.object_id, "code": code})
                continue
            sketches[owner]["constraints"].append({
                "kind": kind, "object_id": record.object_id, "entity_ids": inputs,
                "stored_code": code, "record_offset": record.start,
                "evidence": "explicit stored constraint and repeated entity references",
            })
        except (ValueError, UnicodeError, struct.error):
            continue
    # A radial dimension has both a sketch-owned representation and a reference
    # to a parameter binding owned by the sketch feature.
    for record, body, inputs in dimensions:
        try:
            cursor = len(body) - 27
            binding_id = reference(body, cursor)
            if struct.unpack_from("<I", body, cursor + 11)[0] != 1:
                continue
            target_id = reference(body, cursor + 15)
            target = entities[target_id]
            if target["kind"] != "Circle" or target_id not in inputs:
                continue
            sketch = sketches[target["sketch_object_id"]]
            parameters = [p for p in sketch["parameters"]
                          if p["binding_object_id"] == binding_id and p["role"].startswith("Radial Dimension-")]
            if len(parameters) != 1:
                continue
            parameter = parameters[0]
            sketch["dimensions"].append({
                "kind": "Radius", "object_id": record.object_id, "entity_id": target_id,
                "parameter_name": parameter["parameter_name"], "value_cm": parameter["raw_float64"],
                "value_mm": parameter["hypothesized_value_mm"],
                "expression_candidates": parameter["expression_candidates"],
                "binding_object_id": binding_id, "record_offset": record.start,
            })
        except (ValueError, KeyError, struct.error):
            continue
    return {"unsupported_curves": skipped, "unknown_constraint_codes": unknown_constraints,
            "scope": "Observed point/line/full-circle and H/V/coincident/radius records; not a constraint solver"}
