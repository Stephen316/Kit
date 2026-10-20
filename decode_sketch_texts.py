"""Observed editable rectangle SketchText records from five Fusion 2705 captures.

Reads source text and explicit rectangle/parameter ownership, without exploding
glyphs, rendering fonts, interpreting invariant flags, or evaluating expressions.
"""

import re
import struct

from decode_parameters import decode_stream, read_string
from decode_sketch import attributes, constraint_prefix, numbers, reference, same


TEXT = "E0618268-3A06-450E-9E94-7CF4C2E66802"
RECTANGLE = "8B369926-123F-4F9D-878E-6D4C076128D3"
PARAMETER = "7A6A3D31-BE74-4E19-9115-20642944C2E4"
TEXT_BINDING = "e5460b7b-000b-4a70-ab52-4c2fcc470eb2"
HEIGHT_BINDING = "D91D429C-1BB5-4640-B49F-69AF14F463E9"
POINT = "00D157C2-2332-4BD5-BB53-048C4081D1C3"
POINT_CACHE = "C2CEDAE7-1716-47C1-B7B1-07B70081D0FB"
LINE = "16DEFC4D-1816-4FB0-8E39-9BDA23954248"
LINE_CACHE = "DCA267ED-D615-4934-B64F-AD805E8003E2"
# Their semantics have not been varied. Reject changed opaque controls rather
# than silently returning one of the three observed API styles for a new mode.
OPAQUE_PREFIX = bytes.fromhex("00000000000000f03f0000000000000000000000000000803f")
OPAQUE_LAYOUT = bytes.fromhex(
    "0000000000000000000000f03f00000000000000000000000000000000000000000000f03f000000"
    "0000000000000000000000f03f0000000000000000000000000000f03f0000000000000000000000"
    "0000000000000000000000f03f000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000f03f00000000010000000000000000000000000000803f0000803f0000"
    "000000")
SCOPE = "Five controlled rectangle text variants; other text layouts and opaque controls remain unsupported"


def decode_sketch_texts(data, records, features):
    """Return texts/unresolved; caller may attach each text by sketch_object_id.

    This does not mutate features or require already decoded primitive geometry.
    Only native entity classes are scanned; glyph outlines are never treated as
    source text. Other text layouts and changed opaque fields are rejected.
    """
    text_records = [r for r in records if r.class_guid == TEXT and r.is_primary]
    if not text_records:
        return {"texts": [], "unresolved": [], "scope": SCOPE}
    fragments = {}
    for record in records:
        fragments.setdefault((record.object_id, record.class_guid), []).append(record)
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    numeric, _ = decode_stream(data, records)
    numeric = {p["parameter_object_id"]: p for p in numeric}

    def typed(identity, guid, inherited=False):
        choices = fragments.get((identity, guid), [])
        if len(choices) != 1 or choices[0].is_primary == inherited:
            raise ValueError("Missing or ambiguous typed text support record")
        record = choices[0]
        return record, data[record.body:record.end]

    def binding(identity, guid, owner, expected):
        record, body = typed(identity, guid)
        kind = 1 if guid == TEXT_BINDING else 0
        if (body[:5] != b"\x01\x01\0\0\0" or reference(body, 5) != owner
                or struct.unpack_from("<I", body, 16)[0] != kind or body[20] != 0):
            raise ValueError("Unsupported SketchText binding prefix or owner")
        if kind:
            value, cursor = read_string(body, 21, allow_text_controls=True)
            matches = value == expected
        else:
            value, cursor = numbers(body, 21, 1)[0], 29
            matches = same([value], [expected])
        if not matches or len(body) != cursor + 56:
            raise ValueError("SketchText binding value or suffix mismatch")
        parameter_id = reference(body, cursor)
        index = struct.unpack_from("<I", body, cursor + 11)[0]
        if (body[cursor+15:cursor+19] != bytes(4)
                or reference(body, cursor+19) != owner or body[cursor+30:cursor+33] != b"\x01\0\0"
                or body[cursor+44] != 0 or reference(body, cursor+45) != owner):
            raise ValueError("SketchText binding owner or suffix mismatch")
        bookkeeping = reference(body, cursor+33)
        _, bookkeeping_body = typed(bookkeeping, "6CCF41D5-40BE-48ED-A834-18F3EAED6C57")
        if len(bookkeeping_body) != 39 or reference(bookkeeping_body, 12) != identity:
            raise ValueError("SketchText binding bookkeeping link mismatch")
        return parameter_id, index, record

    def text_parameter(identity, binding_id, index, text):
        record, body = typed(identity, PARAMETER)
        if body[:12] != bytes(7) + b"\x06\0\0\0\0":
            raise ValueError("Unsupported Text model parameter prefix")
        comment, cursor = read_string(body, 12, allow_text_controls=True)
        if struct.unpack_from("<I", body, cursor)[0] != index or reference(body, cursor+4) != binding_id:
            raise ValueError("Text model parameter index/binding mismatch")
        expression, cursor = read_string(body, cursor+15, allow_text_controls=True)
        metadata = body[cursor:cursor+10]
        if metadata != b"\x01" + bytes(9):
            raise ValueError("Unsupported Text model parameter metadata")
        cursor += 10
        role, cursor = read_string(body, cursor)
        value, cursor = read_string(body, cursor, allow_text_controls=True)
        unit, cursor = read_string(body, cursor)
        name, cursor = read_string(body, cursor)
        if (unit != "Text" or value != text or not re.fullmatch(r"Text[0-9]+-Text", role)
                or not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", name)
                or len(body) != cursor+20 or body[cursor:cursor+8] != bytes(8)):
            raise ValueError("Unsupported Text model parameter fields")
        return {"parameter_object_id": identity, "binding_object_id": binding_id,
                "parameter_name": name, "role": role, "text_value": value,
                "expression": expression, "display_units": unit, "comment": comment,
                "stored_parameter_index": index, "expression_metadata_hex": metadata.hex(),
                "uninterpreted_suffix_hex": body[cursor+8:].hex()}

    def rectangle_line(identity, owner):
        _, body = typed(identity, LINE)
        props, cursor = attributes(body, 2)
        if (body[:2] != b"\0\x01" or len(body) != cursor+23 or body[cursor+11] != 0
                or props.get("EntityGenesis") != 0 or props.get("crv_secondary_id") != 0):
            raise ValueError("Unsupported rectangle source line")
        end_id, start_id = reference(body, cursor), reference(body, cursor+12)
        _, cache = typed(identity, LINE_CACHE, True)
        if (len(cache) != 171 or reference(cache, 160) != owner
                or reference(cache, 96) != end_id or reference(cache, 107) != start_id):
            raise ValueError("Rectangle line cache ownership/endpoint mismatch")
        points = []
        for point_id in (start_id, end_id):
            _, point_body = typed(point_id, POINT)
            point_props, point_cursor = attributes(point_body, 2)
            _, point_cache = typed(point_id, POINT_CACHE, True)
            if (point_body[:2] != b"\0\x01" or point_cursor != len(point_body)
                    or point_props.get("EntityGenesis") != 0 or "pt_tag" not in point_props
                    or len(point_cache) != 99 or reference(point_cache, 88) != owner):
                raise ValueError("Unsupported rectangle point/cache ownership")
            points.append(numbers(point_cache, 19, 3))
        vectors = numbers(cache, 0, 12)
        if not same(vectors[:3], points[0]) or not same([a+b for a,b in zip(vectors[:3], vectors[3:6])], points[1]):
            raise ValueError("Rectangle line geometry disagrees with explicit points")
        return {"object_id": identity, "entity_tag": props["crv_primary_id"],
                "start_point_id": start_id, "end_point_id": end_id,
                "start_cm": points[0], "end_cm": points[1],
                "coordinate_system": "sketch-local", "coordinate_units": "cm",
                "is_construction": None, "is_fixed": None,
                "uninterpreted_style_hex": cache[118:160].hex()}

    texts, unresolved = [], []
    for record in text_records:
        try:
            body = data[record.body:record.end]
            props, cursor = attributes(body, 2)
            if (body[:2] != b"\0\x01" or set(props) != {"EntityGenesis", "textex_tag"}
                    or props["EntityGenesis"] != 0):
                raise ValueError("Unsupported SketchText source attributes")
            prefix = body[cursor:cursor+25]
            if prefix != OPAQUE_PREFIX:
                raise ValueError("Unobserved SketchText prefix controls")
            font, cursor = read_string(body, cursor+25)
            if not font or body[cursor] != 0:
                raise ValueError("Unsupported SketchText font/height marker")
            height = numbers(body, cursor+1, 1)[0]
            if height <= 0:
                raise ValueError("Invalid SketchText height")
            height_binding_id = reference(body, cursor+9)
            cursor += 20
            flags = body[cursor:cursor+7]
            if flags[:5] != b"\x01\0\0\0\0" or flags[5] not in (0, 1) or flags[6] != 0:
                raise ValueError("Unsupported SketchText style flags")
            content, cursor = read_string(body, cursor+7, allow_text_controls=True)
            text_binding_id = reference(body, cursor)
            cursor += 11
            tail = body[cursor:]
            if len(tail) != 183 or tail[:5] != b"\x01\0\0\0\0":
                raise ValueError("Unsupported SketchText layout suffix")
            if tail[9:172] != OPAQUE_LAYOUT:
                raise ValueError("Unobserved SketchText opaque layout controls")
            weight = struct.unpack_from("<I", tail, 5)[0]
            if (weight, flags[5]) not in ((400, 0), (700, 0), (400, 1)):
                raise ValueError("Unobserved SketchText formatting combination")
            owner = reference(tail, 172)
            feature = sketches.get(owner)
            if feature is None:
                raise ValueError("SketchText owning sketch reference unresolved")
            controllers = []
            for candidate in records:
                if candidate.class_guid != RECTANGLE or not candidate.is_primary:
                    continue
                candidate_body = data[candidate.body:candidate.end]
                inputs, controller_props, position = constraint_prefix(candidate_body)
                if inputs and inputs[0] == record.object_id:
                    controllers.append((candidate, candidate_body, inputs, controller_props, position))
            if len(controllers) != 1:
                raise ValueError("Missing/ambiguous explicit SketchText rectangle controller")
            controller, rectangle, inputs, controller_props, position = controllers[0]
            if (len(inputs) != 5 or len(set(inputs)) != 5 or controller_props != {"EntityGenesis": 2}
                    or len(rectangle) != position+80 or rectangle[position] != 0
                    or reference(rectangle, position+1) != record.object_id
                    or reference(rectangle, position+12) != owner
                    or rectangle[position+23:position+31] != b"\0\0\0\0\0\x01\0\0"
                    or struct.unpack_from("<I", rectangle, position+31)[0] != 4
                    or rectangle[-1] != 0):
                raise ValueError("Unsupported SketchText rectangle controller")
            line_ids = [reference(rectangle, position+35+11*i) for i in range(4)]
            if line_ids != inputs[1:]:
                raise ValueError("Rectangle controller line lists disagree")
            lines = [rectangle_line(identity, owner) for identity in line_ids]
            for i, line in enumerate(lines):
                if line["end_point_id"] != lines[(i+1) % 4]["start_point_id"]:
                    raise ValueError("Rectangle line incidence is not a closed ordered cycle")
            # A concrete source rectangle is required, rather than inferred glyph bounds.
            edges = [[b-a for a,b in zip(line["start_cm"],line["end_cm"])] for line in lines]
            if (any(sum(x*x for x in edge) <= 1e-20 for edge in edges)
                    or not same([sum(a*b for a,b in zip(edges[0],edges[1]))], [0])
                    or not same(edges[0], [-x for x in edges[2]])
                    or not same(edges[1], [-x for x in edges[3]])):
                raise ValueError("Explicit SketchText support lines do not form a rectangle")
            height_id, height_index, _ = binding(height_binding_id, HEIGHT_BINDING, feature["object_id"], height)
            text_id, text_index, _ = binding(text_binding_id, TEXT_BINDING, feature["object_id"], content)
            height_parameter = numeric[height_id]
            text_parameter_value = text_parameter(text_id, text_binding_id, text_index, content)
            if (height_parameter["declared_binding_object_id"] != height_binding_id
                    or height_parameter["role"] != text_parameter_value["role"][:-4]+"Height"
                    or not same([height_parameter["raw_float64"]], [height])):
                raise ValueError("SketchText height/text parameter roles or values disagree")
            _, feature_body = typed(feature["object_id"], feature["class_guid"])
            count = struct.unpack_from("<I", feature_body, 3)[0]
            if count > 1024:
                raise ValueError("Unsupported sketch feature binding count")
            listed_bindings = [reference(feature_body, 7+11*i) for i in range(count)]
            if height_binding_id not in listed_bindings or text_binding_id not in listed_bindings:
                raise ValueError("Sketch feature does not explicitly own text parameter bindings")
            texts.append({
                "kind": "Text", "object_id": record.object_id, "record_offset": record.start,
                "class_guid": TEXT, "sketch_object_id": owner, "sketch_feature_object_id": feature["object_id"],
                "entity_tag": props["textex_tag"], "text": content, "font_name": font, "height_cm": height,
                "text_style": (1 if weight == 700 else 0) | (2 if flags[5] else 0),
                "text_style_status": "Three captured API style values, bounded by unchanged opaque controls; combined and underline variants unverified",
                "bold": weight == 700, "italic": bool(flags[5]), "native_font_weight": weight,
                "underline": None, "is_horizontal_flip": None, "is_vertical_flip": None,
                "is_fixed": None, "is_reference": None,
                "text_parameter": text_parameter_value,
                "height_parameter": {"parameter_object_id": height_id, "binding_object_id": height_binding_id,
                                     "parameter_name": height_parameter["parameter_name"], "role": height_parameter["role"],
                                     "value_cm": height, "expression_candidates": height_parameter["expression_candidates"],
                                     "stored_parameter_index": height_index},
                "definition": {"kind": "MultiLineTextDefinition", "controller_object_id": controller.object_id,
                               "rectangle_lines": lines, "horizontal_alignment": None, "vertical_alignment": None,
                               "character_spacing_percent": None,
                               "status": "Explicit text/rectangle controller and owned source line/point caches; layout controls unvaried"},
                "uninterpreted": {"prefix_hex": prefix.hex(), "style_flags_hex": flags.hex(),
                                  "layout_suffix_without_weight_or_owner_hex": (tail[:5]+tail[9:172]).hex()},
                "scope": "Observed rectangle SketchText source and reciprocal parameters; no font rendering, glyph decoding or regeneration",
            })
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "class_guid": record.class_guid,
                               "record_offset": record.start, "reason": str(error)})
    return {"texts": texts, "unresolved": unresolved, "scope": SCOPE}
