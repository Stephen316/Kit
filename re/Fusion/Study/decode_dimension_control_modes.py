"""Paired-evidence reference flags for radial, diameter, angle and tangent dims."""

import math
import struct

from decode_dimension_controls import ANGLE, DIAMETER, RADIUS, TANGENT, decode_dimension_controls
from decode_sketch import constraint_prefix


REFERENCE_FLAG_OFFSETS = {RADIUS: 153, DIAMETER: 153, ANGLE: 146, TANGENT: 347}
KINDS = {RADIUS: "Radius", DIAMETER: "Diameter", ANGLE: "Angle", TANGENT: "TangentDistance"}


def decode_dimension_control_modes(data, records, features, dimension_controls=None):
    """Extend only the four newly contrasted native dimension classes.

    Existing annotation decoding proves binding, parameter expression and target
    ownership. New paired API captures prove the class-local reference flag and
    read back annotation positions after using the documented setter.
    """
    if dimension_controls is None:
        dimension_controls = decode_dimension_controls(data, records, features)
    annotation_groups = {}
    for item in dimension_controls["decoded"]:
        annotation_groups.setdefault(item["object_id"], []).append(item)
    annotations = {identity: items[0] for identity, items in annotation_groups.items() if len(items) == 1}
    primary_groups = {}
    for record in records:
        if record.is_primary:
            primary_groups.setdefault(record.object_id, []).append(record)
    primary = {identity: items[0] for identity, items in primary_groups.items() if len(items) == 1}
    decoded, unresolved = [], []
    for feature in features:
        if feature["kind"] != "Sketch":
            continue
        geometry = {item["object_id"]: item for item in feature.get("geometry", [])}
        for dimension in feature.get("dimensions", []):
            record = primary.get(dimension["object_id"])
            if record is None or record.class_guid not in REFERENCE_FLAG_OFFSETS:
                continue
            try:
                annotation = annotations.get(record.object_id)
                if annotation is None or annotation["class_guid"] != record.class_guid:
                    raise ValueError("Dimension annotation/binding/target proof is missing or ambiguous")
                if dimension["kind"] != KINDS[record.class_guid]:
                    raise ValueError("Dimension class and decoded kind disagree")
                observed_kinds = {RADIUS: ["Circle"], DIAMETER: ["Circle"],
                                  ANGLE: ["Line", "Line"], TANGENT: ["Circle", "Circle"]}[record.class_guid]
                if [geometry[identity]["kind"] for identity in dimension["entity_ids"]] != observed_kinds:
                    raise ValueError("Unobserved geometric input variant for this dimension reference flag layout")
                payload = data[record.body:record.end]
                inputs, props, attributes_end = constraint_prefix(payload)
                if props.get("EntityGenesis") != 0 or inputs[1:] != dimension["entity_ids"]:
                    raise ValueError("Unsupported dimension control prefix or target membership")
                offset = attributes_end+REFERENCE_FLAG_OFFSETS[record.class_guid]
                if offset+19 > annotation["value_expression_offset"]-record.body:
                    raise ValueError("Reference/style control fields overlap annotation value text")
                flag = payload[offset]
                if flag not in (0, 1) or payload[offset+17:offset+19] != b"\x01\0":
                    raise ValueError("Unsupported dimension reference/style marker layout")
                style = list(struct.unpack_from("<4f", payload, offset+1))
                if any(not math.isfinite(value) or not 0 <= value <= 1 for value in style):
                    raise ValueError("Unsupported native dimension style component values")
                driving = not bool(flag)
                if "is_driving" in dimension and dimension["is_driving"] != driving:
                    raise ValueError("Dimension driving state disagrees with an earlier verified decoder")
                item = {"object_id": record.object_id, "class_guid": record.class_guid,
                        "kind": dimension["kind"], "sketch_object_id": feature["sketch_object_id"],
                        "binding_object_id": dimension["binding_object_id"],
                        "is_driving": driving, "stored_reference_flag": flag,
                        "reference_flag_offset": record.body+offset,
                        "driving_status": "Matched same-class driving/reference API getter pair; stored reference flag 0 drives and 1 references",
                        "stored_style_components": style,
                        "style_scope": "Four native float32 components retained; their UI/color semantics are not inferred",
                        "annotation_position_cm": annotation["annotation_position_cm"],
                        "annotation_position_offset": annotation["annotation_position_offset"],
                        "annotation_position_evidence": "Observed bounded native field matches actual API textPosition getter after the documented setter in paired fixtures",
                        "stored_value_expression_text": annotation["stored_value_expression_text"],
                        "value_text_scope": "Parameter expression cache; final rendered label and formatting remain outside this decoding"}
                if record.class_guid == TANGENT:
                    item["tangent_side_status"] = "No independent tangent-side contrast or per-side SDK getters; choices remain unresolved"
                decoded.append(item)
            except (ValueError, KeyError, IndexError, struct.error) as error:
                unresolved.append({"object_id": record.object_id, "kind": "DimensionControlModes", "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed radial/diameter/angular/tangent-distance driving-reference flags and getter-verified annotation position layouts; tangent choices and styling remain partial"}
