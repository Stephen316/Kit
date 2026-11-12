"""Observed sketch intersections, Arc inclusion and planar surface projections."""

import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_brep_recipes import decode_recipe
from decode_parameters import read_string
from decode_selection import native_proxy_references
from decode_sketch import ascii_string, attributes, reference
from decode_sketch_projections import CONTROLLER_GUID, ENTRY_GUID, NAME_GUIDS


SURFACE = "A9DB7E42-E095-4A66-BE81-7F36DA04028E"
PROXY = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"
DESCRIPTOR = "5A1BF548-241F-46FD-9FB5-E4B05126EB9D"
CURVE_LEAF = "E2CEFD18-D755-4E09-8E7F-953A2F6D43F8"
POINT_LEAF = "D95DBAC0-238B-4429-A0AD-4AE5BEE79ADF"


def decode_sketch_projection_families(data, records, features):
    """Return old-summary-compatible relationships; one per explicit output."""
    sketches = {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    by_feature = {f["object_id"]: f for f in sketches.values()}
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: matches[0] for identity, matches in grouped.items() if len(matches) == 1}

    def typed(identity, guid=None):
        record = primary.get(identity)
        if record is None or (guid is not None and record.class_guid != guid):
            raise ValueError("Projection-family typed reference unresolved or ambiguous")
        return record, data[record.body:record.end]

    def owned(identity, guid, owner):
        record, payload = typed(identity, guid)
        if reference(payload, len(payload)-11) != owner:
            raise ValueError("Projection-family owned selection disagrees")
        return record, payload

    def source_leaf(identity):
        record, payload = typed(identity)
        if record.class_guid == CURVE_LEAF and len(payload) == 26 and payload[:10] == b"\0"*10:
            sketch_id, tag = struct.unpack_from("<QQ", payload, 10)
            allowed = ("Line", "Circle", "Arc")
        elif record.class_guid == POINT_LEAF and len(payload) == 18 and payload[:2] == b"\0\0":
            sketch_id, tag = struct.unpack_from("<QQ", payload, 2)
            allowed = ("Point",)
        else:
            raise ValueError("Unsupported projection-family source leaf")
        sketch = sketches.get(sketch_id)
        matches = [g for g in (sketch or {}).get("geometry", []) if g.get("entity_tag") == tag and g["kind"] in allowed]
        if sketch is None or len(matches) != 1:
            raise ValueError("Projection-family source sketch/tag unresolved")
        return {"kind": "SketchEntity", "source_leaf_object_id": identity,
                "sketch_object_id": sketch_id, "sketch_name": sketch["name"],
                "entity_object_id": matches[0]["object_id"], "entity_tag": tag, "entity_kind": matches[0]["kind"]}

    def curve_descriptor(identity, owner):
        _, payload = owned(identity, DESCRIPTOR, owner)
        if len(payload) != 263 or payload[:2] != b"\0\0" or struct.unpack_from("<I", payload, 13)[0] != 1:
            raise ValueError("Unsupported projection-family sketch descriptor")
        return source_leaf(reference(payload, 2))

    def source_proxy(identity, owner):
        record, _ = owned(identity, PROXY, owner)
        ids, props = native_proxy_references(data, record)
        if props or len(ids) != 1:
            raise ValueError("Unsupported projection-family source proxy")
        return ids[0], curve_descriptor(ids[0], owner)

    def naming(identity):
        record, payload = typed(identity)
        if record.class_guid not in NAME_GUIDS or payload[:1] != b"\0" or payload[1] not in (0, 1):
            raise ValueError("Unsupported projection-family output name")
        cursor, properties = 2, {}
        if payload[1]:
            count = struct.unpack_from("<I", payload, cursor)[0]
            cursor += 4
            if count > 2:
                raise ValueError("Unsupported projection-family name attributes")
            for _ in range(count):
                key, cursor = ascii_string(payload, cursor)
                kind, cursor = ascii_string(payload, cursor)
                if key in properties:
                    raise ValueError("Duplicate projection-family name attribute")
                if key in ("EdgeEndVertexProgenitor", "EdgeStartVertexProgenitor") and kind == "StrongRefMetaType":
                    value = reference(payload, cursor)
                    typed(value)
                    properties[key] = {"referenced_object_id": value}
                    cursor += 11
                elif key == "progenitor_aux_data" and kind == "BE7E2847-FBC4-4898-A6E7-632A559A7F89":
                    field = struct.unpack_from("<I", payload, cursor)[0]
                    if field != 1:
                        raise ValueError("Unobserved projection auxiliary name field")
                    properties[key] = {"stored_type_guid": kind, "uninterpreted_u32": field,
                                       "scope": "Native auxiliary name data; intersection-root semantics unresolved"}
                    cursor += 4
                else:
                    raise ValueError("Unobserved projection-family output-name attribute kind")
        if len(payload) != cursor+12 or payload[-1] != 0:
            raise ValueError("Unsupported projection-family name suffix")
        return source_leaf(reference(payload, cursor)), properties

    def output(identity, sketch, expected_genesis):
        record, payload = typed(identity)
        props, _ = attributes(payload, 2)
        if (payload[:2] != b"\0\1" or props.get("EntityGenesis") != expected_genesis
                or reference(payload, len(payload)-11) != sketch["sketch_object_id"]):
            raise ValueError("Projection-family output native owner/genesis disagrees")
        matches = [g for g in sketch["geometry"] if g["object_id"] == identity and g["kind"] in ("Point", "Line", "Arc")]
        if len(matches) != 1 or matches[0]["record_offset"] != record.start:
            raise ValueError("Projection-family output primitive cache unresolved")
        geometry = matches[0]
        keys = ("object_id", "sketch_object_id", "kind", "entity_tag", "entity_genesis", "position_cm",
                "start_point_id", "end_point_id", "center_point_id", "start_cm", "end_cm", "center_cm",
                "radius_cm", "normal", "reference_axis", "start_angle_radians", "end_angle_radians",
                "is_fixed", "is_construction", "unrecognized_state_flags")
        result = {k: geometry[k] for k in keys if k in geometry}
        positions = [geometry[k] for k in ("position_cm", "start_cm", "end_cm", "center_cm") if k in geometry]
        in_plane = all(abs(p[2]) <= 1e-9 for p in positions)
        if "normal" in geometry:
            in_plane = in_plane and all(abs(v) <= 1e-9 for v in geometry["normal"][:2])
        result.update(coordinate_system="sketch-local", coordinate_units="cm", is_2d=in_plane,
                      dimensionality_status="Computed from decoded primitive positions/normal in target sketch frame")
        if "is_fixed" not in result:
            result["state_status"] = "Fixed/construction state unresolved for this projected primitive; actual API getters retained in capture evidence"
        return result

    body_summary = None

    def face_proxy(identity, owner):
        nonlocal body_summary
        record, _ = owned(identity, PROXY, owner)
        ids, attrs = native_proxy_references(data, record)
        if attrs or len(ids) != 1:
            raise ValueError("Only observed one-face projection surface supported")
        _, payload = owned(ids[0], "5662F619-2281-4AD9-93DC-1FCFDA1062E7", owner)
        if payload[:4] != b"\0"*4 or struct.unpack_from("<I", payload, 15)[0] != 1:
            raise ValueError("Unsupported projection surface face descriptor")
        namespace, cursor = read_string(payload, 19)
        entity_uuid, cursor = read_string(payload, cursor)
        uuid.UUID(namespace)
        uuid.UUID(entity_uuid)
        if struct.unpack_from("<Q", payload, cursor)[0] != 2:
            raise ValueError("Unsupported projection face association")
        count = struct.unpack_from("<I", payload, cursor+8)[0]
        if count not in (0, 1):
            raise ValueError("Unobserved projection face context count")
        contexts = [reference(payload, cursor+12+11*i) for i in range(count)]
        for context in contexts:
            typed(context, "C46D3EEB-40E1-43FA-83DC-9CB204335417")
        cursor += 12+11*count
        if struct.unpack_from("<I", payload, cursor)[0] != 1 or len(payload)-cursor != 82:
            raise ValueError("Unsupported projection face body anchor/trailer")
        anchor_id = reference(payload, cursor+4)
        body_summary = body_summary or decode_body_selections(data, records)
        anchors = [a for a in body_summary["body_anchors"] if a["object_id"] == anchor_id]
        if len(anchors) != 1:
            raise ValueError("Projection surface historical body unresolved")
        recipe_record, _ = typed(reference(payload, 4), "7ACC2A03-0261-4879-A14A-A93D661A5BDC")
        recipe = decode_recipe(data, recipe_record, primary)
        if recipe["payload_kind"] != "face_recipe_data":
            raise ValueError("Unobserved projection surface recipe kind")
        return {"selection_record_object_id": identity, "descriptor_object_id": ids[0], "recipe": recipe,
                "body_anchor_object_id": anchor_id, "native_body_object_id": anchors[0]["native_body_object_id"],
                "source_owner_object_id": anchors[0]["source_owner_object_id"],
                "context_record_object_ids": contexts,
                "face_identity_scope": "Historical native body and face recipe; exact ASM face mapping and occurrence transforms unresolved"}

    relationships, unresolved = [], []
    for controller in records:
        if not controller.is_primary or controller.class_guid not in (CONTROLLER_GUID, SURFACE):
            continue
        payload = data[controller.body:controller.end]
        try:
            surface = controller.class_guid == SURFACE
            faces, direction, project_type = [], None, None
            if not surface:
                if (len(payload) != 105 or payload[:5] != bytes.fromhex("0000010000")
                        or payload[5] not in (0, 1)):
                    raise ValueError("Unsupported projection-family controller")
                family = struct.unpack_from("<I", payload, 26)[0]
                if family not in (2, 3):
                    raise ValueError("Unobserved projection controller family")
                if family == 3 and payload[5] != 0:
                    continue  # Existing reader owns ordinary Project variants.
                owner = reference(payload, 94)
                if reference(payload, 30) != owner:
                    raise ValueError("Projection-family controller owner copies disagree")
                entry_id, proxy_id = reference(payload, 6), reference(payload, 41)
                descriptor_id, source = source_proxy(proxy_id, owner)
                if family == 3 and source["entity_kind"] != "Arc":
                    continue  # Existing Include Line remains unchanged.
                if family == 2 and (payload[5] != 1 or source["entity_kind"] not in ("Line", "Circle")):
                    raise ValueError("Unobserved sketch intersection source/mode")
                method = "IntersectWithSketchPlane" if family == 2 else "Include"
            else:
                if len(payload) not in (125, 135) or payload[:2] != b"\0\0":
                    raise ValueError("Unsupported surface projection controller")
                code = struct.unpack_from("<I", payload, 2)[0]
                if code == 1 and payload[6] == 0 and len(payload) == 125:
                    cursor, project_type = 7, "ClosestPoint"
                elif code == 0 and len(payload) == 135:
                    direction_id = reference(payload, 6)
                    _, backend = typed(direction_id, "F2A7590D-6654-4674-B393-A2AEF4FEC48A")
                    if (len(backend) != 202 or backend[:6] != bytes.fromhex("000008000000")
                            or struct.unpack_from("<I", backend, 70)[0] != 10
                            or struct.unpack_from("<I", backend, 99)[0] != 1):
                        raise ValueError("Unobserved surface projection direction backend")
                    direction_owner = reference(backend, 191)
                    direction = {"backend_record_object_id": direction_id,
                                 "descriptor_object_id": reference(backend, 103),
                                 "source": curve_descriptor(reference(backend, 103), direction_owner)}
                    if direction["source"]["entity_kind"] != "Line":
                        raise ValueError("Only observed sketch-Line projection direction supported")
                    cursor, project_type = 17, "AlongVector"
                else:
                    raise ValueError("Unobserved surface projection mode/optional direction")
                if struct.unpack_from("<I", payload, cursor)[0] != 1:
                    raise ValueError("Unobserved projection surface count")
                face_id = reference(payload, cursor+4)
                cursor += 15
                if payload[cursor:cursor+4] != bytes.fromhex("01000001"):
                    raise ValueError("Unsupported surface projection entry prefix")
                entry_id = reference(payload, cursor+4)
                cursor += 15
                if struct.unpack_from("<I", payload, cursor+9)[0] != 3:
                    raise ValueError("Unsupported surface projection family marker")
                owner, proxy_id = reference(payload, cursor+13), reference(payload, cursor+24)
                if reference(payload, len(payload)-11) != owner or (direction and direction_owner != owner):
                    raise ValueError("Surface projection owner/direction copies disagree")
                descriptor_id, source = source_proxy(proxy_id, owner)
                if source["entity_kind"] != "Line":
                    raise ValueError("Only observed Line surface projection supported")
                faces = [face_proxy(face_id, owner)]
                method, family = "ProjectToSurface", 3
            target = by_feature.get(owner)
            if target is None:
                raise ValueError("Projection-family target sketch feature unresolved")
            _, entry = typed(entry_id, ENTRY_GUID)
            count = struct.unpack_from("<I", entry, 2)[0]
            if (entry[:2] != b"\0\0" or count not in (1, 2) or len(entry) != 14+19*count
                    or struct.unpack_from("<Q", entry, 6+19*count)[0] != 1):
                raise ValueError("Unsupported projection-family counted output entry")
            if count != (2 if method == "IntersectWithSketchPlane" and source["entity_kind"] == "Circle" else 1):
                raise ValueError("Unobserved projection-family output multiplicity")
            pending = []
            for index in range(count):
                name_id = reference(entry, 6+19*index)
                output_id = struct.unpack_from("<Q", entry, 17+19*index)[0]
                named_source, name_props = naming(name_id)
                if any(source[k] != named_source[k] for k in ("sketch_object_id", "entity_tag", "entity_kind")):
                    raise ValueError("Projection-family input/output naming source disagrees")
                cache = output(output_id, target, 64 if surface else 0)
                expected = "Point" if method == "IntersectWithSketchPlane" else "Line" if surface else "Arc"
                if cache["kind"] != expected:
                    raise ValueError("Unobserved projection-family output primitive")
                pending.append({"controller_object_id": controller.object_id, "entry_object_id": entry_id,
                                "target_feature_object_id": owner, "target_sketch_object_id": target["sketch_object_id"],
                                "target_sketch_name": target["name"], "method": method,
                                "stored_controller_family": family, "is_linked": True,
                                "stored_projection_mode": payload[5] if not surface else None,
                                "source_proxy_object_id": proxy_id, "source_descriptor_object_id": descriptor_id,
                                "output_index": index, "output_count": count, "output_naming_record_object_id": name_id,
                                "output_name_attributes": name_props, "source": source, "output_cache": cache,
                                "surface_project_type": project_type, "surface_selections": faces, "direction": direction,
                                "stored_surface_project_type_code": code if surface else None,
                                "link_status": "Explicit owned controller, counted output/naming, source selection and target cache references"})
            relationships.extend(pending)
        except (ValueError, KeyError, IndexError, UnicodeError, struct.error) as error:
            unresolved.append({"object_id": controller.object_id, "class_guid": controller.class_guid, "reason": str(error)})
    return {"relationships": relationships, "unresolved": unresolved,
            "scope": "Observed primitive intersections, spatial Arc inclusion and planar-face surface projection provenance; no intersection/project solver"}
