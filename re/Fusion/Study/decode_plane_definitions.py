"""Observed parametric plane definitions, ordered supports and cached geometry.

Definition methods come from the owned native backend, independently of the
cached plane-kind field (which conflates offset and offset-through-point).
"""

import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_extrude import optional_reference
from decode_parameters import read_string
from decode_placement import cross, rigid_matrix
from decode_selection import known_construction_entities, native_proxy_references
from decode_sketch import attributes, numbers, reference


# backend code: name, feature variant, cached mode, support roles, scalar role,
#               observed geometry-prefix byte count after ExtraOffset reference.
METHODS = {
    2: ("Offset", 0, 1, ("planarEntity",), "AlongDistance", 171),
    3: ("Angle", 5, 2, ("linearEntity", "planarEntity"), "RotateAngle", 171),
    5: ("Midplane", 3, 4, ("planarEntityOne", "planarEntityTwo"), None, 171),
    8: ("TwoEdges", 7, 5, ("linearEntityOne", "linearEntityTwo"), None, 43),
    11: ("TangentAtPoint", 9, 7, ("tangentFace", "pointEntity"), None, 171),
    12: ("ThreePoints", 2, 6, ("pointEntityOne", "pointEntityTwo", "pointEntityThree"), None, 171),
    15: ("Tangent", 10, 3, ("tangentFace", "planarEntity"), "RotateAngle", 171),
    17: ("OffsetThroughPoint", 0, 1, ("planarEntity", "point"), "AlongDistance", 171),
}


def decode_plane_definitions(data, records, features, *, method_schemas=None, support_resolver=None):
    methods = METHODS if method_schemas is None else {**METHODS, **method_schemas}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: values[0] for identity, values in grouped.items() if len(values) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Plane-definition typed reference unresolved: "+guid)
        return record, data[record.body:record.end]

    def counted(payload, cursor):
        count = struct.unpack_from("<I", payload, cursor)[0]
        if count > 1024 or cursor+4+11*count > len(payload):
            raise ValueError("Unsupported plane-definition reference count")
        identities = [reference(payload, cursor+4+11*i) for i in range(count)]
        if len(set(identities)) != len(identities):
            raise ValueError("Duplicate plane-definition list references")
        return identities, cursor+4+11*count

    def header(feature):
        record, body = typed(feature["object_id"], "D869265F-F339-4751-A066-91D30F81FF08")
        if record.start != feature["record_offset"] or body[:3] != b"\0\0\1":
            raise ValueError("Unsupported plane feature prefix")
        variant = struct.unpack_from("<I", body, 3)[0]
        extra_id, cursor = optional_reference(body, 7)
        if body[cursor] != 1:
            raise ValueError("Unsupported plane feature geometry marker")
        plane_id = reference(body, cursor+1)
        backend_id = reference(body, cursor+12)
        root, cached = typed(plane_id, "8D424E29-DE23-4B1F-A3AD-84C52A497D1A")
        if cached[:2] != b"\0\1":
            raise ValueError("Unsupported plane geometry prefix")
        props, point = attributes(cached, 2)
        if props != {"EntityGenesis": 0} or cached[point+20] != 0:
            raise ValueError("Unsupported plane geometry attributes/marker")
        cached_mode = struct.unpack_from("<I", cached, point)[0]
        coords = numbers(cached, point+21, 9)
        origin, x_axis, y_axis = coords[:3], coords[3:6], coords[6:]
        normal = cross(x_axis, y_axis)
        matrix = rigid_matrix([x_axis[0], y_axis[0], normal[0], origin[0],
                               x_axis[1], y_axis[1], normal[1], origin[1],
                               x_axis[2], y_axis[2], normal[2], origin[2], 0., 0., 0., 1.])
        _, end = read_string(cached, point+109)
        reference(cached, end)
        if (struct.unpack_from("<Q", cached, end+11)[0] != feature["stored_index"]
                or reference(cached, end+20) != feature["object_id"] or cached[end+19] != 0
                or cached[end+31:end+33] != b"\0\1"):
            raise ValueError("Plane native geometry/feature ownership disagrees")
        name, _ = read_string(cached, end+33)
        backend, payload = typed(backend_id, "7B6C3C2D-4096-4E6D-B225-699E8C2D9355")
        if payload[:38] != b"\0"*36+b"\1\0" or reference(payload, len(payload)-11) != feature["object_id"]:
            raise ValueError("Unsupported plane backend prefix/owner")
        backend_extra, start = optional_reference(payload, 38)
        if backend_extra != extra_id:
            raise ValueError("Plane ExtraOffset references disagree")
        geometry_size = 43 if variant == 7 else 171
        method_position = start+geometry_size
        method = struct.unpack_from("<I", payload, method_position)[0]
        schema = methods.get(method)
        if (schema is None or schema[1] != variant or schema[2] != cached_mode or schema[5] != geometry_size
                or payload[method_position+4] != 0):
            raise ValueError("Unobserved plane backend/feature/cache method combination")
        scalar_ids, cursor = counted(payload, method_position+5)
        support_ids, cursor = counted(payload, cursor)
        if len(payload)-cursor != 88 or len(support_ids) != len(schema[3]) or len(scalar_ids) != bool(schema[4]):
            raise ValueError("Unsupported plane backend scalar/support/trailer layout")
        geometry = {"name": name or None, "plane_object_id": plane_id, "plane_definition": schema[0],
                    "origin_cm": origin, "x_axis": x_axis, "y_axis": y_axis, "normal": normal,
                    "plane_to_component_matrix": matrix, "coordinate_units": "cm",
                    "geometry_record_offset": root.start,
                    "coordinate_scope": "Native component cached geometry; occurrence transforms are not inferred"}
        return {"feature": feature, "backend_object_id": backend_id, "method": method, "schema": schema,
                "extra_id": extra_id, "scalar_ids": scalar_ids, "support_ids": support_ids,
                "geometry": geometry, "backend_geometry_prefix_hex": payload[start:method_position].hex()}

    pending, decoded, unresolved = [], [], []
    for feature in features:
        if feature["kind"] != "ConstructionPlane":
            continue
        try:
            candidate = header(feature)
            feature.update(candidate["geometry"])
            pending.append(candidate)
        except (ValueError, UnicodeError, IndexError, KeyError, struct.error) as error:
            unresolved.append({"feature_object_id": feature["object_id"], "reason": str(error)})
    known = known_construction_entities(data, records, features)
    anchors = {a["object_id"]: a for a in decode_body_selections(data, records)["body_anchors"]}

    def face(identity, owner_id):
        record, payload = typed(identity, "5662F619-2281-4AD9-93DC-1FCFDA1062E7")
        if payload[:4] != b"\0"*4 or reference(payload, len(payload)-11) != owner_id:
            raise ValueError("Unsupported plane support face descriptor prefix/owner")
        recipe_id = reference(payload, 4)
        if struct.unpack_from("<I", payload, 15)[0] != 1:
            raise ValueError("Unsupported plane face namespace count")
        namespace, cursor = read_string(payload, 19)
        entity_uuid, cursor = read_string(payload, cursor)
        uuid.UUID(namespace)
        uuid.UUID(entity_uuid)
        if len(namespace) != 36 or len(entity_uuid) != 36 or struct.unpack_from("<Q", payload, cursor)[0] != 2:
            raise ValueError("Unsupported plane face UUID/association header")
        context_ids, cursor = counted(payload, cursor+8)
        if len(context_ids) > 1:
            raise ValueError("Unsupported plane support face context count")
        for context in context_ids:
            typed(context, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
        anchor_ids, cursor = counted(payload, cursor)
        if len(anchor_ids) != 1 or len(payload)-cursor != 67 or anchor_ids[0] not in anchors:
            raise ValueError("Plane support face native body anchor unresolved")
        recipe_record, _ = typed(recipe_id, "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
        recipe = decode_recipe(data, recipe_record, primary)
        if recipe["payload_kind"] not in ("face_recipe_data", "bounded_face_recipe_data"):
            raise ValueError("Unsupported plane face recipe kind")
        anchor = anchors[anchor_ids[0]]
        return {"kind": "Face", "descriptor_object_id": identity, "recipe": recipe,
                "body_anchor_object_id": anchor_ids[0], "native_body_object_id": anchor["native_body_object_id"],
                "source_owner_object_id": anchor["source_owner_object_id"], "context_record_object_ids": context_ids,
                "geometry_status": "Persistent face recipe and native historical body retained; exact ASM face unresolved"}

    def support(identity, role, owner_id):
        if support_resolver is not None:
            resolved = support_resolver(identity, role, owner_id)
            if resolved is not None:
                return resolved
        record = primary.get(identity)
        if record is None:
            raise ValueError("Plane support missing or ambiguous")
        proxy_id = None
        if record.class_guid == "2CA5A1CD-C99B-4C9B-91AF-57989148E841":
            payload = data[record.body:record.end]
            if reference(payload, len(payload)-11) != owner_id:
                raise ValueError("Plane support proxy owner disagrees")
            ids, _ = native_proxy_references(data, record)
            if len(ids) != 1:
                raise ValueError("Only observed single-object plane support proxies supported")
            proxy_id, identity = identity, ids[0]
            record = primary.get(identity)
        if record is None:
            raise ValueError("Plane support descriptor missing or ambiguous")
        if record.class_guid == "5662F619-2281-4AD9-93DC-1FCFDA1062E7":
            entity = face(identity, owner_id)
        else:
            record, payload = typed(identity, "5A1BF548-241F-46FD-9FB5-E4B05126EB9D")
            if (len(payload) != 263 or payload[:2] != b"\0\0"
                    or reference(payload, len(payload)-11) != owner_id
                    or struct.unpack_from("<I", payload, 13)[0] != 1):
                raise ValueError("Unsupported plane native support descriptor layout/owner")
            namespace, cursor = read_string(payload, 17)
            entity_uuid, cursor = read_string(payload, cursor)
            uuid.UUID(namespace)
            uuid.UUID(entity_uuid)
            if len(namespace) != 36 or len(entity_uuid) != 36:
                raise ValueError("Unsupported plane native support UUID lengths")
            terminal_id = reference(payload, 2)
            terminal = primary.get(terminal_id)
            if terminal is None:
                raise ValueError("Plane support native terminal unresolved")
            leaf = data[terminal.body:terminal.end]
            if terminal.class_guid == "90055C05-546C-4EE7-B3C9-3DD922AD0C9C" and len(leaf) == 10 and leaf[:2] == b"\0\0":
                entity_id = struct.unpack_from("<Q", leaf, 2)[0]
                if entity_id not in known:
                    raise ValueError("Plane support native geometry unresolved")
                entity = {"kind": known[entity_id]["kind"], "native_entity": known[entity_id]}
            elif terminal.class_guid == "D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF" and len(leaf) == 18 and leaf[:2] == b"\0\0":
                sketch_id, tag = struct.unpack_from("<QQ", leaf, 2)
                candidates = [(f, g) for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == sketch_id
                              for g in f.get("geometry", []) if g["kind"] == "Point" and g["entity_tag"] == tag]
                if len(candidates) != 1 or "component_position_cm" not in candidates[0][1]:
                    raise ValueError("Plane sketch-point support unresolved or placement unavailable")
                sketch, point = candidates[0]
                entity = {"kind": "SketchPoint", "sketch_object_id": sketch_id, "sketch_name": sketch["name"],
                          "point_object_id": point["object_id"], "point_entity_tag": tag,
                          "component_position_cm": point["component_position_cm"],
                          "coordinate_scope": "Explicit sketch/tag association and decoded native component placement"}
            else:
                raise ValueError("Unobserved plane support terminal class/layout")
            entity.update(descriptor_object_id=identity, terminal_object_id=terminal_id,
                          namespace_text=namespace, entity_guid_text=entity_uuid)
        allowed = (("Face",) if role == "tangentFace" else ("ConstructionPlane", "Face") if role.startswith("planarEntity")
                   else ("ConstructionAxis",) if role.startswith("linearEntity") else ("SketchPoint", "ConstructionPoint"))
        if entity["kind"] not in allowed:
            raise ValueError("Plane support role/type disagreement: "+role)
        return {"role": role, "input_record_object_id": proxy_id or identity,
                "proxy_object_id": proxy_id, "entity": entity}

    for candidate in pending:
        feature = candidate["feature"]
        try:
            parameters = {p["binding_object_id"]: p for p in feature["parameters"]}
            scalars = []
            for identity in candidate["scalar_ids"]:
                parameter = parameters.get(identity)
                if parameter is None or parameter["role"] != candidate["schema"][4]:
                    raise ValueError("Plane definition explicit scalar binding unresolved")
                scalars.append({"role": parameter["role"], "binding_object_id": identity,
                                "value": parameter["raw_float64"], "units": parameter["internal_units"],
                                "activity_scope": ("Stored evaluated offset; the explicit point support defines this method" if candidate["method"] == 17
                                                   else "Observed explicit definition scalar binding")})
            extra_id = candidate["extra_id"]
            extra = parameters.get(extra_id) if extra_id is not None else None
            if extra_id is not None and (extra is None or extra["role"] != "ExtraOffset"):
                raise ValueError("Plane definition ExtraOffset binding unresolved")
            supports = [support(identity, role, feature["object_id"]) for identity, role in
                        zip(candidate["support_ids"], candidate["schema"][3])]
            result = {"feature_object_id": feature["object_id"], "plane_object_id": candidate["geometry"]["plane_object_id"],
                      "backend_object_id": candidate["backend_object_id"], "definition_kind": candidate["schema"][0],
                      "stored_backend_method_code": candidate["method"], "stored_feature_variant_code": candidate["schema"][1],
                      "stored_cached_plane_mode": candidate["schema"][2], "support_inputs": supports,
                      "scalar_parameters": scalars, "extra_offset_binding_object_id": extra_id,
                      "stored_extra_offset_cm": extra["raw_float64"] if extra is not None else None,
                      "extra_offset_scope": "Explicit optional binding retained; general effect is not derived",
                      "cached_geometry": candidate["geometry"],
                      "backend_geometry_prefix_hex": candidate["backend_geometry_prefix_hex"],
                      "backend_prefix_scope": "Observed layout retained; geometry prefix field meanings are not interpreted",
                      "definition_scope": "Observed ordered support roles from the native definition backend, independent of cached plane mode",
                      "geometry_status": "Native cached plane and support identities decoded; parametric geometry is not regenerated"}
            feature["plane_definition_details"] = result
            feature["decode_level"] = "Observed native plane geometry, parametric definition and explicit support roles"
            feature["selection_status"] = "Observed explicit definition support references decoded; face topology remains partial"
            feature["unresolved_inputs"] = (["Exact persistent face-to-ASM mapping"] if any(s["entity"]["kind"] == "Face" for s in supports) else [])
            decoded.append(result)
        except (ValueError, UnicodeError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"feature_object_id": feature["object_id"], "reason": str(error)})
    return {"definitions": decoded, "unresolved": unresolved,
            "scope": "Eight observed parametric plane methods; native component geometry, ordered supports and explicit scalar bindings; no construction regeneration"}
