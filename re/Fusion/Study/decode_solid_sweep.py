"""Observed solid-tool Sweep native identities and numeric caches.

The live API orientation enum and alignment/twist axis role are not inferred
from resulting topology. Explicit native axis identities are retained without
inventing a control flag that distinguishes the captured orientation modes.
"""

from collections import Counter
import math
import struct
import uuid

from decode_body_selections import decode_body_selections
from decode_parameters import read_string
from decode_placement import rigid_matrix, transform_point
from decode_selection import native_origin_axes, native_proxy_references, resolve_single_sketch_curve
from decode_sketch import attributes, reference, same


SWEEP = "FCBB1707-4450-46B3-9E65-0F61682EA8CA"
PROXY = "2CA5A1CD-C99B-4C9B-91AF-57989148E841"
DESCRIPTOR = "5A1BF548-241F-46FD-9FB5-E4B05126EB9D"


def decode_solid_sweep(data, records, body, feature, features):
    if (feature["class_guid"] != SWEEP or len(body) < 180
            or body[0] != 0 or body[1] not in (0, 1)):
        raise ValueError("Unsupported solid Sweep class/prefix")
    props, base = attributes(body, 2) if body[1] else ({}, 2)
    if (props or struct.unpack_from("<I", body, base)[0] != 2
            or body[base+4:base+14] != bytes.fromhex("01030000000000010101")
            or body[base+14:base+38] != b"\0"*24
            or body[base+82] != 0 or body[base+94] != 0
            or struct.unpack_from("<I", body, base+128)[0] != 6
            or struct.unpack_from("<I", body, base+132)[0] != 1):
        raise ValueError("Unsupported observed Cut solid Sweep control layout")
    owner = feature["object_id"]
    grouped = {}
    for record in records:
        if record.is_primary:
            grouped.setdefault(record.object_id, []).append(record)
    primary = {identity: matches[0] for identity, matches in grouped.items() if len(matches) == 1}

    def typed(identity, guid):
        record = primary.get(identity)
        if record is None or record.class_guid != guid:
            raise ValueError("Solid Sweep typed reference unresolved: "+guid)
        return record, data[record.body:record.end]

    def owned(identity, guid):
        record, payload = typed(identity, guid)
        if reference(payload, len(payload)-11) != owner:
            raise ValueError("Solid Sweep input owner disagrees")
        return record, payload

    bindings = {p["binding_object_id"]: p for p in feature["parameters"]}
    values, binding_ids = {}, {}
    for offset, role in ((38, "AgainstDistance"), (49, "AgainstRailDistance"), (60, "AlongDistance"),
                         (71, "AlongRailDistance"), (106, "TaperAngle"), (117, "TwistAngle")):
        identity = reference(body, base+offset)
        binding = bindings.get(identity)
        if binding is None or binding["role"] != role or not math.isfinite(binding["raw_float64"]):
            raise ValueError("Solid Sweep binding/role disagrees: "+role)
        values[role], binding_ids[role] = binding["raw_float64"], identity
    if (not 0 < values["AlongDistance"] <= 1 or values["AgainstDistance"] != 0
            or values["AlongRailDistance"] != 1 or values["AgainstRailDistance"] != 1 or values["TaperAngle"] != 0):
        raise ValueError("Unobserved solid Sweep distance/taper caches")
    control_id = reference(body, base+95)
    _, control = typed(control_id, "B3E4AB56-412B-45EA-85E5-79BE88865B41")
    if len(control) != 85 or reference(control, 6) != owner or reference(control, 74) != owner:
        raise ValueError("Solid Sweep result control owner disagrees")
    path_id = reference(body, base+83)
    path = resolve_single_sketch_curve(data, records, path_id, owner, features, ("Line", "Arc"))

    summary = decode_body_selections(data, records)
    selections = {s["selection_record_object_id"]: s for s in summary["selection_proxies"]}
    descriptors = {d["object_id"]: d for d in summary["body_descriptors"]}
    feature_map = {f["object_id"]: f for f in features}

    def selected_body(identity):
        record, _ = owned(identity, PROXY)
        selected, attrs = native_proxy_references(data, record)
        proxy = selections.get(identity)
        if attrs or len(selected) != 1 or proxy is None or proxy["owner_object_id"] != owner:
            raise ValueError("Solid Sweep owned body proxy unresolved")
        descriptor = descriptors.get(selected[0])
        if descriptor is None or descriptor["owner_object_id"] != owner:
            raise ValueError("Solid Sweep historical body descriptor unresolved")
        source = feature_map.get(descriptor["source_owner_object_id"], {})
        return {"selection_record_object_id": identity, "descriptor_object_id": descriptor["object_id"],
                "native_body_object_id": descriptor["native_body_object_id"],
                "body_anchor_object_id": descriptor["body_anchor_object_id"],
                "source_owner_object_id": descriptor["source_owner_object_id"],
                "source_feature_kind": source.get("kind"), "source_feature_name": source.get("name"),
                "recipe_record_object_id": descriptor["recipe_record_object_id"],
                "context_record_object_ids": descriptor["context_record_object_ids"],
                "identity_scope": "Explicit historical native body; output lifecycle and ASM face identities unresolved"}

    tool = selected_body(reference(body, base+136))
    cursor = base+147
    if body[cursor:cursor+12] != b"\0"*12 or struct.unpack_from("<I", body, cursor+12)[0] != 1:
        raise ValueError("Unobserved solid Sweep result/target list framing")
    target_id = reference(body, cursor+16)
    target = selected_body(target_id)
    if target["native_body_object_id"] == tool["native_body_object_id"]:
        raise ValueError("Solid Sweep tool and target identities coincide")
    namespace, cursor = read_string(body, cursor+27)
    if len(namespace) != 36:
        raise ValueError("Unsupported solid Sweep post-input namespace framing")
    uuid.UUID(namespace)
    if body[cursor:cursor+3] != b"\0"*3:
        raise ValueError("Unsupported solid Sweep dependency prefix")
    count = struct.unpack_from("<I", body, cursor+3)[0]
    if count not in (13, 15) or cursor+7+11*count > len(body):
        raise ValueError("Unobserved solid Sweep dependency count")
    dependencies = [reference(body, cursor+7+11*i) for i in range(count)]
    expected = [control_id, path_id, path["descriptor_object_id"], *binding_ids.values(),
                tool["selection_record_object_id"], tool["descriptor_object_id"],
                target["selection_record_object_id"], target["descriptor_object_id"]]
    if len(set(dependencies)) != len(dependencies) or Counter(expected)-Counter(dependencies):
        raise ValueError("Solid Sweep dependencies omit/duplicate owned controls or selections")
    remaining = [identity for identity in dependencies if identity not in expected]
    axis = None
    if remaining:
        proxies = [identity for identity in remaining if primary.get(identity) and primary[identity].class_guid == PROXY]
        if len(remaining) != 2 or len(proxies) != 1:
            raise ValueError("Unobserved solid Sweep extra dependency roles")
        proxy_id = proxies[0]
        record, _ = owned(proxy_id, PROXY)
        refs, attrs = native_proxy_references(data, record)
        if attrs or len(refs) != 1 or set(remaining) != {proxy_id, refs[0]}:
            raise ValueError("Solid Sweep axis dependency pair disagrees")
        descriptor_id = refs[0]
        _, payload = owned(descriptor_id, DESCRIPTOR)
        if len(payload) != 263 or payload[:2] != b"\0\0" or struct.unpack_from("<I", payload, 13)[0] != 1:
            raise ValueError("Unsupported solid Sweep axis descriptor")
        native_namespace, pos = read_string(payload, 17)
        entity_uuid, _ = read_string(payload, pos)
        uuid.UUID(native_namespace)
        uuid.UUID(entity_uuid)
        terminal_id = reference(payload, 2)
        _, leaf = typed(terminal_id, "90055C05-546C-4EE7-B3C9-3DD922AD0C9C")
        if len(leaf) != 10 or leaf[:2] != b"\0\0":
            raise ValueError("Unsupported solid Sweep native axis leaf")
        axis_id = struct.unpack_from("<Q", leaf, 2)[0]
        entity = native_origin_axes(data, records).get(axis_id)
        if entity is None:
            raise ValueError("Solid Sweep referenced native origin axis unresolved")
        axis = {"selection_record_object_id": proxy_id, "descriptor_object_id": descriptor_id,
                "terminal_object_id": terminal_id, "entity": entity,
                "role_status": "Explicit native axis identity; alignment-versus-twist role encoding unresolved"}
    if values["TwistAngle"] != 0 and axis is None:
        raise ValueError("Unobserved nonzero solid Sweep twist cache without axis selection")
    active_twist = None
    if values["TwistAngle"] != 0 and axis["entity"]["name"] == "X" and path["kind"] == "Line":
        sketches = [f for f in features if f["kind"] == "Sketch" and f["sketch_object_id"] == path["sketch_object_id"]]
        bases = [r for r in records if r.object_id == path["sketch_object_id"]
                 and r.class_guid == "37AD519C-AFB3-4CE2-9E6D-E3269FC6CDB9"]
        if len(sketches) != 1 or len(bases) != 1:
            raise ValueError("Solid twist source sketch context unresolved")
        source = data[bases[0].body:bases[0].end]
        _, collection = typed(reference(source, len(source)-11), "5275CBA4-3D7D-40DC-A651-1DFF3FC8AFBF")
        attrs, pos = attributes(collection, 2)
        member_count = struct.unpack_from("<I", collection, pos)[0]
        if (collection[:2] != b"\0\1" or "crv_tag_id_idx" not in attrs or member_count > 100000
                or pos+4+11*member_count > len(collection)-11):
            raise ValueError("Unsupported solid twist component sketch list")
        members = [reference(collection, pos+4+11*i) for i in range(member_count)]
        component_id = reference(collection, len(collection)-11)
        _, origin = typed(axis["entity"]["origin_container_object_id"], "2972A3B8-3627-49BC-8C3D-18707605EC44")
        origin_count = struct.unpack_from("<I", origin, 4)[0]
        if (members.count(path["sketch_object_id"]) != 1 or origin[:4] != b"\0"*4
                or origin_count != 7 or len(origin) != 19+11*origin_count
                or reference(origin, len(origin)-11) != component_id
                or [reference(origin, 8+11*i) for i in range(origin_count)].count(axis["entity"]["object_id"]) != 1):
            raise ValueError("Solid twist axis/path native component ownership disagrees")
        sketch = sketches[0]
        curves = [g for g in sketch["geometry"] if g["object_id"] == path["curve_object_id"] and g["kind"] == "Line"]
        if len(curves) != 1:
            raise ValueError("Solid twist straight source geometry unresolved")
        matrix = rigid_matrix(sketch["placement"]["sketch_to_component_matrix"])
        points = [transform_point(matrix, curves[0][key]) for key in ("start_cm", "end_cm")]
        # Captured axis is native X. Other axes/offset or non-Line paths retain
        # numeric caches, but do not acquire this bounded activity annotation.
        if all(same(point[1:], axis["entity"]["origin_cm"][1:]) for point in points) and points[1][0] > points[0][0]:
            active_twist = {"angle_radians": values["TwistAngle"], "axis_selection": axis,
                            "component_object_id": component_id,
                            "evidence_status": "Nonzero native TwistAngle and sole explicit X-axis selection; identical-source0/30/60deg API/input/native/volume contrasts prove geometric activity",
                            "scope": "Observed Cut schema with straight positive-X Line collinear with origin axis in same native component; public twistAngle getter remains None"}
    return {"operation": "Cut", "stored_operation_code": 2, "sweep_mode": "SolidBody",
            "stored_mode_code": 6, "is_solid": bool(body[base+11]),
            "solid_body": tool, "profile": {"kind": "Body", "body_selection": tool},
            "input_bodies": [target], "path": path, "path_fraction": values["AlongDistance"],
            "distance_two_fraction": None, "stored_parameter_values": values, "parameter_bindings": binding_ids,
            "orientation": None, "solid_orientation": None,
            "solid_orientation_status": "Native orientation enum unresolved; captured live Perpendicular=0/Rigid=1 both reimport as0; mode6 establishes solid input only",
            "solid_axis_selection": axis,
            "solid_aligned_axis": None, "solid_twist_axis": None,
            "axis_role_status": "Native origin-axis reference retained when present; no role inferred solely from nonzero twist or resulting topology",
            "taper_angle_radians": None, "twist_angle_radians": None,
            "stored_twist_angle_radians": values["TwistAngle"],
            "active_solid_twist": active_twist,
            "twist_status": "Public twistAngle getter returns None; native cache matches input and controlled0/30/60deg same-geometry captures prove geometric effect with explicit X axis; native axis-role encoding unresolved",
            "guide_rail": None, "guide_surfaces": [],
            "dependency_record_object_ids": dependencies,
            "result_control_record_object_id": control_id,
            "uninterpreted_result_control_prefix_hex": control[:6].hex(),
            "input_selection_status": "Observed solid tool and historical target plus sketch Line/Arc path and optional native origin axis; no swept geometry reconstruction"}
