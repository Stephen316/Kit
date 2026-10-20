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
        if kind not in ("IntrinsicMetaTypeuint64", "IntrinsicMetaTypedouble") or key in result:
            raise ValueError("Unsupported attribute layout")
        result[key] = struct.unpack_from("<Q" if kind == "IntrinsicMetaTypeuint64" else "<d", data, position)[0]
        if kind == "IntrinsicMetaTypedouble" and not math.isfinite(result[key]):
            raise ValueError("Non-finite numeric attribute")
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
    from decode_nurbs import decode_splines

    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    for sketch in sketches.values():
        sketch.update({"coordinate_system": "sketch-local", "coordinate_units": "cm",
                       "geometry": [], "constraints": [], "dimensions": [], "internal_associations": []})
    entities, curves, skipped = {}, [], []
    for record in records:
        body = data[record.body:record.end]
        if not body.startswith(b"\0\x01"):
            continue
        try:
            props, cursor = attributes(body, 2)
            if props.get("EntityGenesis") not in (0, 2, 64, 128, 130, 256, 258, 512):
                continue
            owner = reference(body, len(body) - 11)
            if owner not in sketches:
                continue
            item = {"object_id": record.object_id, "sketch_object_id": owner,
                    "record_offset": record.start, "entity_genesis": props["EntityGenesis"]}
            if "pt_tag" in props and len(body) - cursor == 99:
                item.update({"kind": "Point", "entity_tag": props["pt_tag"],
                             "position_cm": numbers(body, cursor + 19, 3)})
                entities[record.object_id] = item
            elif "crv_primary_id" in props and props.get("EntityGenesis") in (0, 2, 128, 130, 256, 258, 512):
                curves.append((record, body, props, cursor, item))
        except (ValueError, UnicodeError, struct.error):
            continue
    spline_entities, spline_skipped = decode_splines(data, records, sketches, entities)
    entities.update(spline_entities)
    skipped.extend(spline_skipped)
    offset_side_ids = {r.object_id for r in records if r.class_guid == "04e598ff-2979-5e41-8bc0-5c435c810909"}
    for record, body, props, cursor, item in curves:
        try:
            auxiliary_parent = None
            offset_curve, offset_side = False, None
            if ((record.class_guid == "DCA267ED-D615-4934-B64F-AD805E8003E2" and len(body)-cursor == 182)
                    or (record.class_guid == "F0130424-8B7E-4092-93C9-1CA807482534" and len(body)-cursor == 173)):
                try:
                    offset_side = reference(body, len(body)-48)
                    offset_curve = offset_side in offset_side_ids
                except ValueError:
                    pass
            if len(body) - cursor == 182 and not offset_curve:
                try:
                    parent = reference(body, cursor)
                    if parent in {r.object_id for r, *_ in curves}:
                        auxiliary_parent = parent
                        cursor += 11
                except ValueError:
                    pass
            values = numbers(body, cursor, 12)
            origin = values[:3]
            if props.get("crv_secondary_id") != 0 and not (offset_curve and props["EntityGenesis"] == 512):
                raise ValueError("Secondary curve representation is unsupported")
            if offset_curve:
                item.update(offset_side_record_object_id=offset_side,
                            secondary_entity_tag=props["crv_secondary_id"],
                            secondary_tag_status="Observed offset representation; secondary tag semantics unresolved")
            if len(body) - cursor == 171 or (offset_curve and record.class_guid == "DCA267ED-D615-4934-B64F-AD805E8003E2"):
                first = reference(body, cursor + 96)
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
                if auxiliary_parent is not None:
                    item["auxiliary_parent_id"] = auxiliary_parent
            elif len(body) - cursor in (162, 182) or (offset_curve and record.class_guid == "F0130424-8B7E-4092-93C9-1CA807482534"):
                first = reference(body, cursor + 96)
                center = entities[first]
                normal, axis = values[3:6], values[6:9]
                if center["sketch_object_id"] != item["sketch_object_id"] or not same(center["position_cm"], origin):
                    raise ValueError("Circle center reference does not match")
                if (values[9] <= 0 or not same([sum(x*x for x in normal), sum(x*x for x in axis),
                                     sum(x*y for x, y in zip(normal, axis))], [1, 1, 0])):
                    raise ValueError("Invalid circular representation")
                item.update({"kind": "Circle", "center_point_id": first, "center_cm": origin,
                             "radius_cm": values[9], "radius_mm": values[9] * 10,
                             "normal": normal, "reference_axis": axis})
                if len(body) - cursor == 182:
                    end_id = reference(body, cursor + 107)
                    start_id = reference(body, cursor + 118)
                    cross = [normal[1]*axis[2]-normal[2]*axis[1],
                             normal[2]*axis[0]-normal[0]*axis[2],
                             normal[0]*axis[1]-normal[1]*axis[0]]
                    for identity, angle in ((start_id, values[10]), (end_id, values[11])):
                        expected = [o + values[9] * (math.cos(angle)*a + math.sin(angle)*c)
                                    for o, a, c in zip(origin, axis, cross)]
                        if (entities[identity]["sketch_object_id"] != item["sketch_object_id"]
                                or not same(entities[identity]["position_cm"], expected)):
                            raise ValueError("Arc endpoint reference disagrees with angular geometry")
                    item.update({"kind": "Arc", "start_point_id": start_id, "end_point_id": end_id,
                                 "start_cm": entities[start_id]["position_cm"],
                                 "end_cm": entities[end_id]["position_cm"],
                                 "start_angle_radians": values[10], "end_angle_radians": values[11]})
                elif not same(values[10:], [0, 2 * math.pi]):
                    raise ValueError("Unsupported circular parameter interval")
            elif len(body) - cursor == 192:
                values = numbers(body, cursor, 13)
                center_id = reference(body, cursor + 104)
                center = entities[center_id]
                if (center["sketch_object_id"] != item["sketch_object_id"]
                        or not same(center["position_cm"], origin)
                        or not 0 < values[10] <= values[9]
                        or not same([sum(x*x for x in values[3:6]), sum(x*x for x in values[6:9]),
                                     sum(x*y for x, y in zip(values[3:6], values[6:9]))], [1, 1, 0])):
                    raise ValueError("Unsupported ellipse representation")
                item.update({"kind": "Ellipse", "center_point_id": center_id, "center_cm": origin,
                             "major_radius_cm": values[9], "minor_radius_cm": values[10],
                             "stored_major_axis": values[3:6], "stored_minor_axis": values[6:9]})
                if same(values[11:], [0, 2 * math.pi]):
                    item.update(major_axis_entity_id=reference(body, cursor+116),
                                minor_axis_entity_id=reference(body, cursor+127))
                else:
                    end_id, start_id = reference(body, cursor+115), reference(body, cursor+128)
                    if not 0 < values[12]-values[11] <= 2*math.pi:
                        raise ValueError("Unsupported elliptical arc interval")
                    for identity, angle in ((start_id, values[11]), (end_id, values[12])):
                        expected = [o+values[9]*math.cos(angle)*a+values[10]*math.sin(angle)*b
                                    for o, a, b in zip(origin, values[3:6], values[6:9])]
                        if (entities[identity]["sketch_object_id"] != item["sketch_object_id"]
                                or not same(entities[identity]["position_cm"], expected)):
                            raise ValueError("Elliptical arc endpoint disagrees with geometry")
                    item.update(kind="EllipticalArc", start_point_id=start_id, end_point_id=end_id,
                                start_cm=entities[start_id]["position_cm"], end_cm=entities[end_id]["position_cm"],
                                start_angle_radians=values[11], end_angle_radians=values[12])
            else:
                raise ValueError("Unrecognized curve record size")
            item["entity_tag"] = props["crv_primary_id"]
            # These boolean fields occupy the same observed style suffix for
            # lines, circles, arcs and ellipses, including ellipse axis lines.
            fixed = struct.unpack_from("<I", body, len(body) - 51)[0]
            construction = struct.unpack_from("<I", body, len(body) - 46)[0]
            if offset_curve:
                item["state_status"] = "Offset curve fixed/construction state layout unresolved"
            elif fixed in (0, 1) and construction in (0, 1):
                item.update(is_fixed=bool(fixed), is_construction=bool(construction))
            else:
                item["unrecognized_state_flags"] = [fixed, construction]
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
                dimensions.append((record, body, inputs, cursor))
                continue
            if props.get("EntityGenesis") != 2:
                continue
            if (record.class_guid == "24DB790E-3DCD-4336-AFA3-6F119EF2239B"
                    and body[cursor:cursor+3] == b"\0\x01\x01"):
                cursor += 3
            owner = reference(body, cursor)
            if owner not in sketches:
                continue
            cursor += 11
            code = struct.unpack_from("<Q", body, cursor)[0]
            count = struct.unpack_from("<I", body, cursor + 8)[0]
            if count != len(inputs):
                raise ValueError("Constraint argument copies differ")
            copied = [reference(body, cursor + 12 + 11*i) for i in range(count)]
            if sorted(copied) != sorted(inputs) or any(i not in entities or entities[i]["sketch_object_id"] != owner for i in inputs):
                raise ValueError("Constraint entity references do not resolve")
            # The first list is dependency order; the second preserves argument roles.
            dependency_order = inputs
            inputs = copied
            kinds = [entities[i]["kind"] for i in inputs]
            if code == 2147483648:
                splines = [entities[i] for i in inputs if entities[i]["kind"] == "ControlPointSpline"]
                lines = [entities[i] for i in inputs if entities[i]["kind"] == "Line"]
                if len(splines) == 1 and len(lines)+1 == len(inputs):
                    points = splines[0]["nurbs"]["control_points_cm"]
                    segments = list(zip(points, points[1:]))
                    for line in lines:
                        matches = [index for index, (a, b) in enumerate(segments)
                                   if (same(line["start_cm"], a) and same(line["end_cm"], b))
                                   or (same(line["start_cm"], b) and same(line["end_cm"], a))]
                        if len(matches) != 1:
                            break
                        segments.pop(matches[0])
                    else:
                        if not segments:
                            sketches[owner]["internal_associations"].append({
                                "kind": "SplineControlPolygon", "object_id": record.object_id,
                                "stored_code": code, "entity_ids": inputs, "spline_entity_id": splines[0]["object_id"],
                                "scope": "Internal spline/control polygon membership; not a user geometric constraint"})
                            continue
            kind = {1: "Coincident", 2: "Collinear", 4: "Concentric", 16: "Parallel",
                    32: "Perpendicular", 64: "Horizontal", 128: "Vertical", 256: "Tangent", 512: "Smooth",
                    1024: "Symmetry", 2048: "Equal", 4096: "MidPoint"}.get(code)
            if kind in ("Horizontal", "Vertical") and kinds == ["Point", "Point"]:
                kind += "Points"
            valid = {
                "Horizontal": kinds == ["Line"], "Vertical": kinds == ["Line"],
                "HorizontalPoints": kinds == ["Point", "Point"],
                "VerticalPoints": kinds == ["Point", "Point"],
                "Coincident": len(kinds) == 2 and "Point" in kinds,
                "Parallel": kinds == ["Line", "Line"], "Perpendicular": kinds == ["Line", "Line"],
                "Collinear": kinds == ["Line", "Line"],
                "Concentric": len(kinds) == 2 and all(k in ("Circle", "Arc", "Ellipse") for k in kinds),
                "Tangent": len(kinds) == 2 and all(k != "Point" for k in kinds),
                "Smooth": len(kinds) == 2 and all(k != "Point" for k in kinds),
                "Equal": kinds == ["Line", "Line"] or (len(kinds) == 2 and all(k in ("Circle", "Arc") for k in kinds)),
                "MidPoint": sorted(kinds) == ["Line", "Point"],
                "Symmetry": len(kinds) == 3 and kinds[0] == kinds[1] and kinds[2] == "Line",
            }
            if not valid.get(kind, False):
                unknown_constraints.append({"object_id": record.object_id, "code": code})
                continue
            sketches[owner]["constraints"].append({
                "kind": kind, "object_id": record.object_id, "entity_ids": inputs,
                "dependency_entity_ids": dependency_order,
                "stored_code": code, "record_offset": record.start,
                "evidence": "explicit stored constraint and repeated entity references",
            })
        except (ValueError, UnicodeError, struct.error):
            continue
    # A radial dimension has both a sketch-owned representation and a reference
    # to a parameter binding owned by the sketch feature.
    unsupported_dimensions = []
    for record, body, inputs, attributes_end in dimensions:
        parameter = None
        try:
            target_count = len(inputs) - 1
            if not 1 <= target_count <= 2:
                continue
            cursor = len(body) - (16 + 11 * target_count)
            binding_id = reference(body, cursor)
            if struct.unpack_from("<I", body, cursor + 11)[0] != target_count:
                continue
            targets = [reference(body, cursor + 15 + index*11) for index in range(target_count)]
            if targets != inputs[1:] or any(i not in entities for i in targets):
                continue
            sketch = sketches[entities[targets[0]]["sketch_object_id"]]
            if any(entities[i]["sketch_object_id"] != sketch["sketch_object_id"] for i in targets):
                continue
            parameters = [p for p in sketch["parameters"]
                          if p["binding_object_id"] == binding_id and " Dimension-" in p["role"]]
            if len(parameters) != 1:
                continue
            parameter = parameters[0]
            code = struct.unpack_from("<Q", body, cursor-8)[0]
            kind = {0x4000: "Linear", 0x8000: "Angle", 0x10000: "Diameter", 0x20000: "Radius",
                    0x400000: "Linear", 0x800000: "Linear", 0x1000000: "EllipseMajorRadius",
                    0x2000000: "EllipseMinorRadius", 0x8000000: "ConcentricCircle",
                    0x200000000: "LinearDiameter", 0x4000000000: "TangentDistance"}.get(code)
            kinds = [entities[i]["kind"] for i in targets]
            if code == 0x4000 and kinds in (["Line", "Point"], ["Line", "Line"]):
                kind = "Offset"
            valid = {
                "Radius": kinds in (["Circle"], ["Arc"]), "Diameter": kinds in (["Circle"], ["Arc"]),
                "Linear": kinds == ["Point", "Point"], "Angle": kinds == ["Line", "Line"],
                "Offset": kinds in (["Line", "Point"], ["Line", "Line"]),
                "EllipseMajorRadius": kinds == ["Ellipse"], "EllipseMinorRadius": kinds == ["Ellipse"],
                "ConcentricCircle": len(kinds) == 2 and all(k in ("Circle", "Arc") for k in kinds),
                "LinearDiameter": kinds in (["Line", "Point"], ["Line", "Line"]),
                "TangentDistance": len(kinds) == 2 and kinds[0] in ("Point", "Line", "Circle", "Arc") and kinds[1] in ("Circle", "Arc"),
            }
            if not valid.get(kind, False):
                raise ValueError("Unsupported dimension code or target kinds: "+str(code))
            dimension = {
                "kind": kind, "object_id": record.object_id, "entity_ids": targets,
                "parameter_name": parameter["parameter_name"], "raw_value": parameter["raw_float64"],
                "expression_candidates": parameter["expression_candidates"],
                "binding_object_id": binding_id, "record_offset": record.start,
                "stored_kind_code": code, "driving_status": "Undecoded for this dimension class",
            }
            if kind == "Linear":
                dimension["orientation"] = {0x4000: "Aligned", 0x400000: "Horizontal", 0x800000: "Vertical"}[code]
            if kind == "Offset":
                dimension["orientation"] = "PerpendicularToFirstLine"
            if record.class_guid == "8C780195-72C0-4a56-A911-E43AB14357F2":
                driven_flag = body[attributes_end+129]
                if driven_flag in (0, 1):
                    dimension.update(is_driving=not bool(driven_flag),
                                     driving_status="Observed dimension reference flag decoded")
            if kind == "TangentDistance":
                dimension["tangent_sides_status"] = "Tangent-side choices remain undecoded"
            if kind == "Angle":
                dimension.update(value_radians=parameter["raw_float64"], value_degrees=parameter["hypothesized_value_degrees"])
            else:
                dimension.update(value_cm=parameter["raw_float64"], value_mm=parameter["hypothesized_value_mm"])
            if len(targets) == 1:
                dimension["entity_id"] = targets[0]
            sketch["dimensions"].append(dimension)
        except (ValueError, KeyError, IndexError, struct.error) as error:
            if parameter is not None:
                unsupported_dimensions.append({"object_id": record.object_id, "reason": str(error)})
            continue
    from decode_sketch_tools import decode_sketch_tools
    tools = decode_sketch_tools(data, records, sketches, entities)
    return {"unsupported_curves": skipped, "unknown_constraint_codes": unknown_constraints,
            "tool_constraints": tools,
            "unsupported_dimensions": unsupported_dimensions,
            "scope": "Observed primitives, NURBS, conics, geometric constraints and dimensions; not a constraint solver"}
