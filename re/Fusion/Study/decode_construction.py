"""Observed custom construction axis/point geometry and reciprocal ownership."""

import math
import struct

from decode_parameters import read_string
from decode_sketch import attributes, numbers, reference


def decode_construction(data, records, features):
    decoded, unresolved = [], []
    for feature in features:
        kind = feature["kind"]
        if kind not in ("ConstructionAxis", "ConstructionPoint"):
            continue
        source = next(r for r in records if r.start == feature["record_offset"])
        body = data[source.body:source.end]
        try:
            root_id = reference(body, 6 if kind == "ConstructionAxis" else 11)
            choices = []
            for root in records:
                if root.object_id != root_id:
                    continue
                chunk = data[root.body:root.end]
                try:
                    if chunk[:2] != b"\0\x01":
                        continue
                    props, cursor = attributes(chunk, 2)
                    if props != {"EntityGenesis": 0}:
                        continue
                    position = numbers(chunk, cursor, 3)
                    label_offset = cursor+(64 if kind == "ConstructionAxis" else 24)
                    _, end = read_string(chunk, label_offset)
                    reference(chunk, end)
                    index = struct.unpack_from("<Q", chunk, end+11)[0]
                    if index != feature["stored_index"] or reference(chunk, end+20) != feature["object_id"]:
                        continue
                    if chunk[end+19] != 0 or chunk[end+31:end+33] != b"\0\x01":
                        continue
                    name, _ = read_string(chunk, end+33)
                    item = {"name": name or None, "coordinate_units": "cm",
                            "geometry_record_offset": root.start,
                            "decode_level": "Observed native geometry and reciprocal feature ownership",
                            "unresolved_inputs": ["Parametric construction input geometry references"],
                            "coordinate_scope": "Native component; assembly occurrence transforms unresolved"}
                    if kind == "ConstructionAxis":
                        direction = numbers(chunk, cursor+24, 3)
                        if not math.isclose(sum(v*v for v in direction), 1., abs_tol=1e-9):
                            continue
                        item.update(axis_object_id=root_id, origin_cm=position, direction=direction)
                    else:
                        item.update(point_object_id=root_id, position_cm=position)
                    choices.append(item)
                except (ValueError, UnicodeError, IndexError, struct.error):
                    continue
            if len(choices) != 1:
                raise ValueError("Construction geometry is unresolved or ambiguous")
            feature.update(choices[0])
            decoded.append({"object_id": feature["object_id"], "kind": kind})
        except (ValueError, IndexError, struct.error) as error:
            unresolved.append({"object_id": feature["object_id"], "kind": kind, "reason": str(error)})
    return {"decoded": decoded, "unresolved": unresolved,
            "scope": "Observed named axis/point native geometry; parametric input definitions remain partial"}
