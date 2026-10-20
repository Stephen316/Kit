"""Observed local component/occurrence graph and composed sketch coordinates.

Definitions and native occurrences are distinct. Repeated component instances
reuse definitions; nested paths compose their parent-local rigid transforms.
External links, flexible components, joints and general feature ownership are
not interpreted here.
"""

import struct

from decode_parameters import read_string
from decode_placement import IDENTITY, rigid_matrix, transform_point, transform_vector
from decode_sketch import attributes, numbers, reference
from fusion_metadata import Reader


COMPONENT_GUID = "42054630-20A0-40E1-B969-CFE9E742F5C9"
OCCURRENCE_GUID = "CE2913AA-CFE0-4F04-9102-24424ED3BCFA"
OCCURRENCE_COLLECTION_GUID = "904F885E-D859-4755-A7EF-6EBED8732FAD"
SKETCH_COLLECTION_GUID = "5275CBA4-3D7D-40DC-A651-1DFF3FC8AFBF"
SKETCH_BASE_GUID = "37AD519C-AFB3-4CE2-9E6D-E3269FC6CDB9"


def multiply(a, b):
    return rigid_matrix([sum(a[row*4+k]*b[k*4+column] for k in range(4))
                         for row in range(4) for column in range(4)])


def component_label(body, identity):
    candidates = []
    for cursor in range(max(0, len(body)-4)):
        if body[cursor:cursor+4] != b"\x24\0\0\0":
            continue
        try:
            guid, position = read_string(body, cursor)
            name, end = read_string(body, position)
            if len(guid) != 36 or body[end:end+1] != b"\0":
                continue
            root_occurrence = None
            if len(body)-end == 2 and body[end+1] == 0:
                pass
            elif len(body)-end == 12:
                root_occurrence = reference(body, end+1)
            else:
                continue
            candidates.append({"object_id": identity, "name": name or None,
                               "native_guid_text": guid, "root_occurrence_object_id": root_occurrence,
                               "name_scope": "Stored native label; root may contain only a document display suffix"})
        except (ValueError, UnicodeError, struct.error):
            continue
    if len(candidates) != 1:
        raise ValueError("Component label/identity suffix unresolved or ambiguous")
    return candidates[0]


def occurrence(body, identity):
    reader = Reader(body)
    explicit_name = reader.string()
    chunk = body[reader.position:]
    if chunk[:5] != b"\x01\x01\0\0\0":
        raise ValueError("Unsupported occurrence prefix")
    component_id = reference(chunk, 5)
    number = struct.unpack_from("<I", chunk, 27)[0]
    namespace, cursor = read_string(chunk, 31)
    instance_guid, cursor = read_string(chunk, cursor)
    if cursor != 183 or len(namespace) != 36 or len(instance_guid) != 36:
        raise ValueError("Unsupported occurrence identity strings")
    if (chunk[183] != 1 or chunk[192:199] != b"\0\x01\x01\0\0\0\0"
            or reference(chunk, 199) != component_id):
        raise ValueError("Occurrence component-reference copies disagree")
    if chunk[210] == 1:
        matrix, cursor = list(IDENTITY), 211
    elif chunk[210] == 0:
        matrix, cursor = rigid_matrix(numbers(chunk, 211, 16)), 339
    else:
        raise ValueError("Unsupported occurrence transform flag")
    if chunk[cursor:cursor+9] != b"\0"*9:
        raise ValueError("Unsupported occurrence transform suffix")
    cursor += 9
    if chunk[cursor] == 0:
        parent, cursor = None, cursor+1
    else:
        parent, cursor = reference(chunk, cursor), cursor+11
    if cursor != len(chunk):
        raise ValueError("Unconsumed occurrence payload")
    if (parent is None) != (explicit_name == "rootInstance") or (parent is not None and number == 0):
        raise ValueError("Unsupported occurrence root/instance identity")
    return {"object_id": identity, "component_object_id": component_id,
            "instance_number": number, "explicit_name": explicit_name or None,
            "namespace_text": namespace, "instance_guid_text": instance_guid,
            "parent_collection_object_id": parent, "local_transform": matrix,
            "translation_units": "cm", "matrix_order": "row-major; column-vector multiplication"}


def collection(body, identity):
    if body[:3] != b"\0\0\x01" or body[11:18] != b"\0\x01\x01\0\0\0\0":
        raise ValueError("Unsupported occurrence collection prefix")
    count = struct.unpack_from("<I", body, 18)[0]
    if count > 100000 or len(body) != 33+11*count:
        raise ValueError("Unsupported occurrence collection size")
    members = [reference(body, 22+11*i) for i in range(count)]
    if len(set(members)) != count:
        raise ValueError("Duplicate native occurrences in component collection")
    return {"object_id": identity, "component_object_id": reference(body, len(body)-11),
            "occurrence_object_ids": members}


def world_sketch(sketch, matrix):
    placement = sketch.get("placement", {}).get("sketch_to_component_matrix")
    if placement is None:
        raise ValueError("Owned sketch placement is unresolved")
    transform = multiply(matrix, placement)
    geometry = []
    for entity in sketch["geometry"]:
        item = {"object_id": entity["object_id"], "kind": entity["kind"]}
        for key in ("position_cm", "start_cm", "end_cm", "center_cm", "apex_cm"):
            if key in entity:
                item[key] = transform_point(transform, entity[key])
        for key in ("normal", "reference_axis", "stored_major_axis", "stored_minor_axis"):
            if key in entity:
                item[key] = transform_vector(transform, entity[key])
        for key in ("radius_cm", "major_radius_cm", "minor_radius_cm"):
            if key in entity:
                item[key] = entity[key]
        if "nurbs" in entity:
            item["control_points_cm"] = [transform_point(transform, p) for p in entity["nurbs"]["control_points_cm"]]
        geometry.append(item)
    return {"sketch_object_id": sketch["sketch_object_id"], "name": sketch["name"],
            "sketch_to_world_matrix": transform, "geometry": geometry,
            "scope": "Root-component world coordinates through this occurrence path"}


def decode_assembly(data, records, features):
    components, occurrences, collections, unresolved = {}, {}, {}, []
    for record in records:
        try:
            body = data[record.body:record.end]
            if record.class_guid == COMPONENT_GUID:
                components[record.object_id] = component_label(body, record.object_id)
            elif record.class_guid == OCCURRENCE_GUID:
                if record.payload_start is None:
                    raise ValueError("Occurrence requires a complete indexed payload")
                occurrences[record.object_id] = occurrence(data[record.payload_start:record.end], record.object_id)
            elif record.class_guid == OCCURRENCE_COLLECTION_GUID:
                collections[record.object_id] = collection(body, record.object_id)
        except (ValueError, UnicodeError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    owned, sketches = {}, {f["sketch_object_id"]: f for f in features if f["kind"] == "Sketch"}
    for record in records:
        if record.class_guid != SKETCH_COLLECTION_GUID:
            continue
        try:
            body = data[record.body:record.end]
            props, cursor = attributes(body, 2)
            if "crv_tag_id_idx" not in props:
                continue
            owner = reference(body, len(body)-11)
            if owner not in components:
                raise ValueError("Sketch collection component is unresolved")
            count = struct.unpack_from("<I", body, cursor)[0]
            if count > 100000 or cursor+4+count*11 > len(body)-11:
                raise ValueError("Truncated component sketch collection")
            for index in range(count):
                sketch_id = reference(body, cursor+4+index*11)
                if sketch_id not in sketches:
                    continue
                bases = [r for r in records if r.object_id == sketch_id and r.class_guid == SKETCH_BASE_GUID]
                if len(bases) != 1 or reference(data[bases[0].body:bases[0].end], bases[0].end-bases[0].body-11) != record.object_id:
                    raise ValueError("Sketch/component reciprocal ownership does not resolve")
                if sketch_id in owned:
                    raise ValueError("Sketch appears in multiple component collections")
                owned[sketch_id] = owner
                sketches[sketch_id].update(component_object_id=owner, component_name=components[owner]["name"],
                                           component_association="Explicit sketch collection and reciprocal owner reference")
                if "placement" in sketches[sketch_id]:
                    sketches[sketch_id]["placement"]["scope"] = "Native parent component; see assembly occurrence paths for world coordinates"
        except (ValueError, KeyError, IndexError, struct.error) as error:
            unresolved.append({"object_id": record.object_id, "reason": str(error)})
    paths, root_sketches = [], []
    try:
        by_component = {}
        for item in collections.values():
            owner = item["component_object_id"]
            if owner not in components or owner in by_component:
                raise ValueError("Occurrence collection component is unresolved or ambiguous")
            by_component[owner] = item
            for identity in item["occurrence_object_ids"]:
                entry = occurrences.get(identity)
                if entry is None or entry["parent_collection_object_id"] != item["object_id"]:
                    raise ValueError("Occurrence/parent collection reciprocal references disagree")
        for entry in occurrences.values():
            parent_id = entry["parent_collection_object_id"]
            if parent_id is not None and (parent_id not in collections or entry["object_id"] not in collections[parent_id]["occurrence_object_ids"]):
                raise ValueError("Occurrence is absent from its declared parent collection")
        roots = [o for o in occurrences.values() if o["parent_collection_object_id"] is None]
        if len(roots) != 1 or roots[0]["component_object_id"] not in components:
            raise ValueError("Unique document root occurrence is unresolved")
        root = roots[0]

        def visit(component_id, parent_matrix, path, ancestors):
            if component_id in ancestors or len(ancestors) > 128 or len(paths) > 10000:
                raise ValueError("Cyclic or excessive assembly expansion")
            if component_id not in by_component:
                raise ValueError("Component occurrence collection is missing")
            for identity in by_component[component_id]["occurrence_object_ids"]:
                entry = occurrences[identity]
                child = components.get(entry["component_object_id"])
                if child is None:
                    raise ValueError("Occurrence component definition is unresolved")
                name = entry["explicit_name"] or str(child["name"])+":"+str(entry["instance_number"])
                full_path = path+"+"+name if path else name
                world = multiply(parent_matrix, entry["local_transform"])
                item = {"path": full_path, "name": name, "native_occurrence_object_id": identity,
                        "component_object_id": child["object_id"], "component_name": child["name"],
                        "parent_component_object_id": component_id, "local_transform": entry["local_transform"],
                        "world_transform": world,
                        "sketches": [world_sketch(sketches[i], world) for i, owner in owned.items() if owner == child["object_id"]]}
                paths.append(item)
                visit(child["object_id"], world, full_path, ancestors|{component_id})

        visit(root["component_object_id"], root["local_transform"], "", set())
        root_sketches = [world_sketch(sketches[i], root["local_transform"]) for i, owner in owned.items()
                         if owner == root["component_object_id"]]
    except (ValueError, KeyError, IndexError, struct.error) as error:
        unresolved.append({"reason": str(error)})
    for feature in features:
        sources = {owned[s["sketch_object_id"]] for s in feature.get("sketch_reference_candidates", [])
                   if s["sketch_object_id"] in owned}
        if sources:
            feature["source_sketch_components"] = [{"object_id": i, "name": components[i]["name"]} for i in sorted(sources)]
            feature["component_ownership_status"] = "Input sketch context known; general feature ownership not decoded"
    return {"components": list(components.values()), "native_occurrences": list(occurrences.values()),
            "occurrence_collections": list(collections.values()), "occurrence_paths": paths,
            "root_sketches": root_sketches, "unresolved": unresolved,
            "scope": "Observed local definitions, repeated/nested instances and owned sketch coordinates",
            "limitations": ["No external component resolution, flexible assembly, joints or grounding semantics.",
                            "Source-sketch ownership does not establish general modeling-feature ownership."]}
