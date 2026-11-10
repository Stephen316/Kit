"""Observed sketch dimension annotation tails and class-bounded driving flags.

The existing false/true reference contrast belongs to the shared linear
dimension class. Other dimension classes do not inherit that flag inference.
Annotation positions were compared with saved API creation arguments; the
original captures did not read back post-creation textPosition properties.
"""

import math
import struct

from decode_parameters import read_string
from decode_sketch import constraint_prefix, numbers, reference


LINEAR = "8C780195-72C0-4a56-A911-E43AB14357F2"
RADIUS = "8EDAC24D-35D4-4591-B8E7-B3EA081C9DF0"
DIAMETER = "664AD49F-207F-4CD5-8555-DD269E9F09EA"
ANGLE = "6EEAFDE5-59C4-424D-8EBE-77CDBC562017"
TANGENT = "A9E23439-6F4F-4ED3-A610-319F0AFABEED"
TAIL_SIZES = {LINEAR: 52, RADIUS: 32, DIAMETER: 32, ANGLE: 32, TANGENT: 32}


def decode_dimension_controls(data, records, features):
    """Return annotation controls for already decoded sketch dimensions.

    Native kind, binding and target lists are checked again. Positions use the
    sketch coordinate system. Value text is retained as an expression cache,
    without claiming it is the final rendered label or the user's formatting.
    """
    groups = {}
    for record in records:
        if record.is_primary:
            groups.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in groups.items() if len(values) == 1}
    decoded, unresolved = [], []
    for feature in features:
        if feature["kind"] != "Sketch":
            continue
        geometry = {item["object_id"]: item for item in feature.get("geometry", [])}
        for dimension in feature.get("dimensions", []):
            identity = dimension["object_id"]
            try:
                record = primary.get(identity)
                if record is None or record.class_guid not in TAIL_SIZES:
                    raise ValueError("Dimension annotation class missing, ambiguous or unsupported")
                payload = data[record.body:record.end]
                inputs, props, attributes_end = constraint_prefix(payload)
                if props.get("EntityGenesis") != 0:
                    raise ValueError("Only observed ordinary dimension control attributes supported")
                targets = dimension["entity_ids"]
                if inputs[1:] != targets or any(target not in geometry for target in targets):
                    raise ValueError("Dimension input targets disagree with the decoded sketch geometry")
                count = len(targets)
                binding_position = len(payload)-(16+11*count)
                binding_id = reference(payload, binding_position)
                if (binding_id != dimension["binding_object_id"]
                        or struct.unpack_from("<I", payload, binding_position+11)[0] != count
                        or [reference(payload, binding_position+15+11*i) for i in range(count)] != targets
                        or payload[-1] != 0
                        or struct.unpack_from("<Q", payload, binding_position-8)[0] != dimension["stored_kind_code"]):
                    raise ValueError("Dimension type/binding/target tail disagrees")
                parameters = [item for item in feature["parameters"] if item["binding_object_id"] == binding_id]
                binding = primary.get(binding_id)
                if (len(parameters) != 1 or binding is None
                        or binding.class_guid != "D91D429C-1BB5-4640-B49F-69AF14F463E9"):
                    raise ValueError("Dimension parameter binding is missing, ambiguous or of an unsupported class")
                parameter = parameters[0]
                binding_payload = data[binding.body:binding.end]
                if (len(binding_payload) != 85 or reference(binding_payload, 5) != feature["object_id"]
                        or not math.isclose(numbers(binding_payload, 21, 1)[0], parameter["raw_float64"], abs_tol=1e-12)):
                    raise ValueError("Dimension parameter owner/value association disagrees")
                position_offset = binding_position-TAIL_SIZES[record.class_guid]
                if position_offset < attributes_end:
                    raise ValueError("Dimension annotation position overlaps its prefix")
                point = numbers(payload, position_offset, 3)
                # Bound the UTF-16 value text by its known ending, not by an
                # arbitrary occurrence of plausible text elsewhere in a record.
                candidates = []
                for start in range(max(attributes_end, position_offset-2052), position_offset-3):
                    try:
                        text, end = read_string(payload, start)
                    except (ValueError, UnicodeError, struct.error):
                        continue
                    if end == position_offset and text and text in parameter["expression_candidates"]:
                        candidates.append((start, text))
                if len(candidates) != 1:
                    raise ValueError("Unique bounded annotation value-expression field was not established")
                text_offset, text = candidates[0]
                item = {"object_id": identity, "kind": dimension["kind"], "class_guid": record.class_guid,
                        "sketch_object_id": feature["sketch_object_id"], "sketch_feature_object_id": feature["object_id"],
                        "binding_object_id": binding_id, "parameter_name": parameter["parameter_name"],
                        "entity_ids": targets, "stored_kind_code": dimension["stored_kind_code"],
                        "annotation_position_cm": point, "annotation_position_offset": record.body+position_offset,
                        "position_scope": "Observed sketch-coordinate text-position field; compared with saved API creation arguments",
                        "stored_value_expression_text": text, "value_expression_offset": record.body+text_offset,
                        "value_text_evidence": "Bounded native text field agrees exactly with the explicitly bound numeric parameter expression",
                        "uninterpreted_annotation_tail_hex": payload[position_offset+24:binding_position-8].hex(),
                        "driving_status": "No driving/reference contrast captured for this dimension class"}
                if record.class_guid == LINEAR:
                    flag = payload[attributes_end+129]
                    if flag not in (0, 1):
                        raise ValueError("Unsupported shared linear-dimension reference flag")
                    item.update(is_driving=not bool(flag), stored_reference_flag=flag,
                                driving_status="Existing matched driving/driven API contrast for this shared linear dimension class")
                    if "is_driving" in dimension and dimension["is_driving"] != item["is_driving"]:
                        raise ValueError("Dimension driving state disagrees with the existing decoder")
                elif record.class_guid in (RADIUS, DIAMETER):
                    symbol, end = read_string(payload, text_offset-6)
                    if end != text_offset or symbol != ("R" if record.class_guid == RADIUS else "Ø"):
                        raise ValueError("Unobserved radial/diameter annotation symbol field")
                    item.update(stored_annotation_prefix_text=symbol,
                                prefix_evidence="Explicit length-prefixed UTF-16 symbol field precedes the value-expression text")
                if record.class_guid == TANGENT:
                    item["tangent_side_status"] = "No contrasting tangent-side API settings captured; side flags remain uninterpreted"
                decoded.append(item)
            except (ValueError, UnicodeError, IndexError, KeyError, struct.error) as error:
                unresolved.append({"object_id": identity, "kind": "DimensionControls", "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed annotation positions/value-expression caches and existing class-bounded driving state; formatting, unsupported driving flags and tangent choices remain partial"}
